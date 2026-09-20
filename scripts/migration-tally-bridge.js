#!/usr/bin/env node
"use strict";

/**
 * Migration-mode local Tally bridge.
 *
 * Runs on the same machine as TallyPrime, reads masters and Voucher Register
 * from localhost:9000, and uploads parsed data to the migration backend.
 *
 * Usage examples:
 *   node tally-integration/scripts/migration-tally-bridge.js --endpoint=http://localhost:3000/api/tally/bridge/upload --token=replace_me --company="My Company"
 *   node tally-integration/scripts/migration-tally-bridge.js --endpoint=http://localhost:3000/api/tally/bridge/upload --token=replace_me --replace-chart --from=2025-04-01 --to=2026-03-31
 *
 * Required:
 *   --endpoint=... or TALLY_BRIDGE_ENDPOINT
 *   --token=... or TALLY_BRIDGE_TOKEN
 *
 * Optional:
 *   --tally-url=http://localhost:9000  (default)
 *   --company="Exact company name"     (defaults to first company from List of Companies)
 *   --replace-chart                     (requests account chart replacement before ledger import)
 *   --from=YYYY-MM-DD                  (voucher range start, default: 365 days ago)
 *   --to=YYYY-MM-DD                    (voucher range end, default: today)
 */

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const args = {
    endpoint: process.env.TALLY_BRIDGE_ENDPOINT || "",
    token: process.env.TALLY_BRIDGE_TOKEN || "",
    tallyUrl: process.env.TALLY_URL || "http://localhost:9000",
    company: "",
    replaceChart: false,
    from: "",
    to: "",
  };
  for (const raw of argv) {
    if (raw === "--replace-chart") args.replaceChart = true;
    else if (raw.startsWith("--endpoint=")) args.endpoint = raw.slice("--endpoint=".length);
    else if (raw.startsWith("--token=")) args.token = raw.slice("--token=".length);
    else if (raw.startsWith("--tally-url=")) args.tallyUrl = raw.slice("--tally-url=".length);
    else if (raw.startsWith("--company=")) args.company = raw.slice("--company=".length);
    else if (raw.startsWith("--from=")) args.from = raw.slice("--from=".length);
    else if (raw.startsWith("--to=")) args.to = raw.slice("--to=".length);
    else if (raw === "--help" || raw === "-h") {
      console.log("Use --endpoint, --token, optional --company, --replace-chart, --from, --to, --tally-url");
      process.exit(0);
    }
  }
  return args;
}

function isoToday() {
  return new Date().toISOString().slice(0, 10);
}

function isoDaysAgo(days) {
  return new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
}

function assertIsoDate(value, name) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) fail(`${name} must be YYYY-MM-DD`);
}

function xmlEscape(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function toTallyDate(iso) {
  return String(iso).replace(/-/g, "");
}

function readTag(block, tagName) {
  const match = new RegExp(`<${tagName}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tagName}>`, "i").exec(block);
  if (!match) return "";
  return match[1]
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .trim();
}

function readAllTags(block, tagName) {
  return [...block.matchAll(new RegExp(`<${tagName}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tagName}>`, "gi"))].map((m) => m[1]);
}

function parseSignedAmount(rawValue) {
  const raw = String(rawValue || "");
  const amount = parseFloat(raw.replace(/[^0-9.-]/g, "")) || 0;
  return /cr\b/i.test(raw) && amount > 0 ? -amount : amount;
}

async function postXml(url, xml) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "text/xml" },
    body: xml,
    signal: AbortSignal.timeout ? AbortSignal.timeout(30000) : undefined,
  });
  if (!response.ok) {
    const preview = (await response.text().catch(() => "")).slice(0, 200);
    throw new Error(`Tally request failed (${response.status}) ${preview}`.trim());
  }
  return response.text();
}

function listCompaniesXml() {
  return `<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>List of Companies</ID></HEADER><BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION NAME="List of Companies" ISMODIFY="No"><TYPE>Company</TYPE><NATIVEMETHOD>NAME</NATIVEMETHOD></COLLECTION></TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>`;
}

function ledgerCollectionXml(company) {
  return `<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>LedColl</ID></HEADER><BODY><DESC><STATICVARIABLES><SVCURRENTCOMPANY>${xmlEscape(company)}</SVCURRENTCOMPANY><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION NAME="LedColl" ISMODIFY="No"><TYPE>Ledger</TYPE><FETCH>NAME,PARENT,OPENINGBALANCE,CLOSINGBALANCE,GSTIN,INCOMETAXNUMBER,LEDGERPHONE,EMAIL,GUID,ALTERID</FETCH></COLLECTION></TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>`;
}

function groupCollectionXml(company) {
  return `<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>GrpColl</ID></HEADER><BODY><DESC><STATICVARIABLES><SVCURRENTCOMPANY>${xmlEscape(company)}</SVCURRENTCOMPANY><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION NAME="GrpColl" ISMODIFY="No"><TYPE>Group</TYPE><FETCH>NAME,PARENT,ISREVENUE,GUID,ALTERID</FETCH></COLLECTION></TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>`;
}

function voucherRegisterXml(company, fromDate, toDate) {
  return `<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE><ID>Voucher Register</ID></HEADER><BODY><DESC><STATICVARIABLES><SVCURRENTCOMPANY>${xmlEscape(company)}</SVCURRENTCOMPANY><SVFROMDATE TYPE="Date">${toTallyDate(fromDate)}</SVFROMDATE><SVTODATE TYPE="Date">${toTallyDate(toDate)}</SVTODATE><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES></DESC></BODY></ENVELOPE>`;
}

function parseCompanies(xml) {
  const names = [];
  for (const match of xml.matchAll(/<COMPANY\s[^>]*\bNAME="([^"]*)"/gi)) {
    if (match[1].trim()) names.push(match[1].trim());
  }
  for (const block of readAllTags(xml, "COMPANY")) {
    const name = readTag(block, "NAME").trim();
    if (name) names.push(name);
  }
  return [...new Set(names)];
}

function parseLedgers(xml) {
  return [...xml.matchAll(/<LEDGER(\s[^>]*)?>([\s\S]*?)<\/LEDGER>/gi)]
    .map(([, attrs, block]) => {
      const nameAttr = attrs ? /\bNAME="([^"]*)"/i.exec(attrs)?.[1] : "";
      return {
        name: (nameAttr || readTag(block, "NAME")).trim(),
        parent: readTag(block, "PARENT").trim(),
        openingBalance: parseSignedAmount(readTag(block, "OPENINGBALANCE")),
        closingBalance: parseFloat(readTag(block, "CLOSINGBALANCE").replace(/[^0-9.-]/g, "")) || 0,
        gstin: readTag(block, "GSTIN") || undefined,
        pan: readTag(block, "INCOMETAXNUMBER") || undefined,
        phone: readTag(block, "LEDGERPHONE") || undefined,
        email: readTag(block, "EMAIL") || undefined,
        tallyGuid: readTag(block, "GUID") || undefined,
        tallyAlterId: readTag(block, "ALTERID") || undefined,
      };
    })
    .filter((row) => row.name);
}

function parseGroups(xml) {
  return [...xml.matchAll(/<GROUP(\s[^>]*)?>([\s\S]*?)<\/GROUP>/gi)]
    .map(([, attrs, block]) => {
      const nameAttr = attrs ? /\bNAME="([^"]*)"/i.exec(attrs)?.[1] : "";
      return {
        name: (nameAttr || readTag(block, "NAME")).trim(),
        parent: readTag(block, "PARENT").trim(),
        isRevenue: readTag(block, "ISREVENUE").toLowerCase() === "yes",
        tallyGuid: readTag(block, "GUID") || undefined,
        tallyAlterId: readTag(block, "ALTERID") || undefined,
      };
    })
    .filter((row) => row.name);
}

function fromTallyDate(value) {
  const text = String(value || "").trim();
  if (text.length !== 8) return isoToday();
  return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}`;
}

function parseVouchers(xml) {
  return readAllTags(xml, "VOUCHER")
    .map((block) => {
      const date = fromTallyDate(readTag(block, "DATE"));
      const entries = [
        ...block.matchAll(/<(ALLLEDGERENTRIES\.LIST|LEDGERENTRIES\.LIST|ACCOUNTINGALLOCATIONS\.LIST)>([\s\S]*?)<\/\1>/gi),
      ]
        .map(([, , entry]) => ({
          ledgerName: readTag(entry, "LEDGERNAME").trim(),
          amount: parseFloat(readTag(entry, "AMOUNT").replace(/[^0-9.-]/g, "")) || 0,
        }))
        .filter((entry) => entry.ledgerName);
      if (!entries.length) return null;
      return {
        date,
        voucherType: readTag(block, "VOUCHERTYPENAME").trim(),
        voucherNumber: readTag(block, "VOUCHERNUMBER").trim(),
        partyLedgerName: readTag(block, "PARTYLEDGERNAME").trim(),
        narration: readTag(block, "NARRATION").trim(),
        tallyGuid: readTag(block, "GUID") || undefined,
        tallyRemoteId: readTag(block, "REMOTEID") || undefined,
        tallyAlterId: readTag(block, "ALTERID") || undefined,
        entries,
      };
    })
    .filter(Boolean);
}

async function uploadBridge(endpoint, token, payload) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout ? AbortSignal.timeout(300000) : undefined,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `Bridge upload failed (${response.status})`);
  }
  return body;
}

async function main() {
  if (typeof fetch !== "function") fail("Node.js 18+ is required (built-in fetch missing)");

  const args = parseArgs(process.argv.slice(2));
  const fromDate = args.from || isoDaysAgo(365);
  const toDate = args.to || isoToday();

  if (!args.endpoint.trim()) fail("Missing endpoint. Use --endpoint=... or set TALLY_BRIDGE_ENDPOINT");
  if (!args.token.trim()) fail("Missing token. Use --token=... or set TALLY_BRIDGE_TOKEN");
  assertIsoDate(fromDate, "from");
  assertIsoDate(toDate, "to");

  console.log(`Connecting to Tally: ${args.tallyUrl}`);
  const companyXml = await postXml(args.tallyUrl, listCompaniesXml());
  const companies = parseCompanies(companyXml);
  if (!companies.length) fail("No companies found in Tally. Ensure a company is open in TallyPrime.");

  const company = args.company.trim() || companies[0];
  if (!companies.includes(company)) {
    fail(`Company \"${company}\" was not found. Available companies: ${companies.join(", ")}`);
  }
  console.log(`Using company: ${company}`);

  const [ledgerXml, groupXml, voucherXml] = await Promise.all([
    postXml(args.tallyUrl, ledgerCollectionXml(company)),
    postXml(args.tallyUrl, groupCollectionXml(company)),
    postXml(args.tallyUrl, voucherRegisterXml(company, fromDate, toDate)),
  ]);

  const ledgers = parseLedgers(ledgerXml);
  const groups = parseGroups(groupXml);
  const vouchers = parseVouchers(voucherXml).filter((row) => row.date >= fromDate && row.date <= toDate);

  if (!ledgers.length && !vouchers.length) {
    fail("No ledgers or vouchers were parsed from Tally responses.");
  }

  console.log(`Parsed ${ledgers.length} ledgers, ${groups.length} groups, ${vouchers.length} vouchers`);
  const result = await uploadBridge(args.endpoint, args.token, {
    company,
    replaceChart: args.replaceChart,
    fromDate,
    toDate,
    ledgers,
    groups,
    vouchers,
  });

  console.log("Upload complete:");
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  fail(error instanceof Error ? error.message : String(error));
});
