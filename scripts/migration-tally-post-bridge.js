#!/usr/bin/env node
"use strict";

/**
 * Migration-mode local Tally posting bridge.
 *
 * Pulls queued vouchers from the backend, posts each voucher to local Tally,
 * and reports posting results back to the backend.
 *
 * Usage:
 *   node tally-integration/scripts/migration-tally-post-bridge.js --endpoint=http://localhost:3000 --token=replace_me --company="My Company"
 *
 * Required:
 *   --endpoint=... or TALLY_BRIDGE_ENDPOINT
 *   --token=... or TALLY_BRIDGE_TOKEN
 *
 * Optional:
 *   --company="Exact company name"
 *   --tally-url=http://localhost:9000
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
    company: process.env.TALLY_COMPANY || "",
  };
  for (const raw of argv) {
    if (raw.startsWith("--endpoint=")) args.endpoint = raw.slice("--endpoint=".length);
    else if (raw.startsWith("--token=")) args.token = raw.slice("--token=".length);
    else if (raw.startsWith("--tally-url=")) args.tallyUrl = raw.slice("--tally-url=".length);
    else if (raw.startsWith("--company=")) args.company = raw.slice("--company=".length);
    else if (raw === "--help" || raw === "-h") {
      console.log("Use --endpoint, --token, optional --company, --tally-url");
      process.exit(0);
    }
  }
  return args;
}

function timeoutSignal(ms) {
  if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
    return AbortSignal.timeout(ms);
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ms);
  if (typeof timeout.unref === "function") timeout.unref();
  return controller.signal;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function escapeXml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function toTallyDate(isoDate) {
  return String(isoDate || "").replace(/-/g, "");
}

function normalizeEndpointBase(endpoint) {
  const clean = String(endpoint || "").trim().replace(/\/+$/, "");
  if (!clean) return "";
  if (clean.endsWith("/api/tally/bridge/upload")) {
    return clean.slice(0, -"/api/tally/bridge/upload".length);
  }
  if (clean.endsWith("/api/tally/bridge")) {
    return clean.slice(0, -"/api/tally/bridge".length);
  }
  return clean;
}

async function fetchJson(url, token, options = {}) {
  const response = await fetch(url, {
    method: options.method || "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    signal: timeoutSignal(options.timeoutMs || 60000),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `HTTP ${response.status} for ${url}`);
  }
  return body;
}

async function postTallyXml(tallyUrl, xml) {
  const response = await fetch(tallyUrl, {
    method: "POST",
    headers: { "Content-Type": "text/xml" },
    body: xml,
    signal: timeoutSignal(45000),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`Tally request failed (${response.status}) ${text.slice(0, 220)}`);
  }
  return text;
}

function ledgerNamesCollectionXml(company) {
  return `<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>LedNameColl</ID></HEADER><BODY><DESC><STATICVARIABLES><SVCURRENTCOMPANY>${escapeXml(company)}</SVCURRENTCOMPANY><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION NAME="LedNameColl" ISMODIFY="No"><TYPE>Ledger</TYPE><FETCH>NAME</FETCH></COLLECTION></TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>`;
}

function parseLedgerNames(xml) {
  return [...xml.matchAll(/<LEDGER(\s[^>]*)?>([\s\S]*?)<\/LEDGER>/gi)]
    .map(([, attrs, block]) => {
      const nameAttr = attrs ? /\bNAME="([^"]*)"/i.exec(attrs)?.[1] : "";
      const nameTag = /<NAME>([^<]*)<\/NAME>/i.exec(block)?.[1];
      return String(nameAttr || nameTag || "").replace(/&amp;/g, "&").trim();
    })
    .filter(Boolean);
}

function createLedgerXml(company, name, parentGroup) {
  return `<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>All Masters</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY>${escapeXml(company)}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC><REQUESTDATA><TALLYMESSAGE><LEDGER NAME="${escapeXml(name)}" ACTION="Create"><NAME>${escapeXml(name)}</NAME><PARENT>${escapeXml(parentGroup)}</PARENT></LEDGER></TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>`;
}

// Default parent group for our fixed internal control-account ledger names; anything else
// (typically a vendor name) falls back to Sundry Creditors when auto-creating for purchase vouchers.
const KNOWN_LEDGER_GROUPS = {
  "purchase accounts": "Purchase Accounts",
  "local purchase": "Purchase Accounts",
  "interstate purchase": "Purchase Accounts",
  "input gst": "Duties & Taxes",
  "rounding off": "Indirect Expenses",
  "tds payable": "Duties & Taxes",
  "sundry creditors": "Sundry Creditors",
};

async function ensureLedgersExist(args, vouchers) {
  const purchaseVouchers = vouchers.filter((voucher) => voucher.sourceType === "purchase_invoice");
  if (purchaseVouchers.length === 0) return;
  const company = String(args.company || purchaseVouchers[0].company || "").trim();
  if (!company) return;
  console.log("Checking Tally ledgers for purchase vouchers...");
  const existingXml = await postTallyXml(args.tallyUrl, ledgerNamesCollectionXml(company));
  const existingNames = new Set(parseLedgerNames(existingXml).map((name) => name.toLowerCase()));
  const neededNames = new Set();
  for (const voucher of purchaseVouchers) {
    for (const leg of Array.isArray(voucher.legs) ? voucher.legs : []) {
      const name = String(leg.ledgerName || "").trim();
      if (name) neededNames.add(name);
    }
  }
  for (const name of neededNames) {
    if (existingNames.has(name.toLowerCase())) continue;
    const parentGroup = KNOWN_LEDGER_GROUPS[name.toLowerCase()] || "Sundry Creditors";
    console.log(`Creating missing ledger "${name}" under "${parentGroup}"...`);
    try {
      const result = await postTallyXml(args.tallyUrl, createLedgerXml(company, name, parentGroup));
      const created = parseTagNumber(result, "CREATED");
      const exceptions = parseTagNumber(result, "EXCEPTIONS");
      if (created > 0 && exceptions === 0) {
        existingNames.add(name.toLowerCase());
      } else {
        console.log(`  Could not auto-create "${name}": ${parseLineError(result) || "unknown error"}`);
      }
    } catch (error) {
      console.log(`  Could not auto-create "${name}": ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}

function parseTagNumber(xml, tagName) {
  const match = new RegExp(`<${tagName}>([^<]+)</${tagName}>`, "i").exec(xml);
  return match ? Number(match[1]) || 0 : 0;
}

function parseLineError(xml) {
  const match = /<LINEERROR>([\s\S]*?)<\/LINEERROR>/i.exec(xml);
  return match ? match[1].replace(/\s+/g, " ").trim() : "";
}

function voucherXml(voucher, fallbackCompany) {
  const company = String(voucher.company || fallbackCompany || "").trim();
  const narration = String(voucher.narration || "").trim();
  const reference = String(voucher.reference || "").trim();
  const fullNarration = reference ? `${narration} | Ref: ${reference}` : narration;
  const voucherType = String(voucher.voucherType || "Journal").trim();
  const date = String(voucher.date || "").trim();
  const remoteId = String(voucher.remoteId || "").trim();
  if (!company) throw new Error("Voucher company is required");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error("Voucher date must be YYYY-MM-DD");
  if (!remoteId) throw new Error("Voucher remoteId is required");

  const legs = Array.isArray(voucher.legs) ? voucher.legs : [];
  if (legs.length < 2) throw new Error("Voucher requires at least two legs");
  let signedSum = 0;
  const legXml = legs.map((leg) => {
    const ledgerName = String(leg.ledgerName || "").trim();
    const drcr = String(leg.drcr || "").trim();
    const absAmount = Math.abs(Number(leg.amount || 0));
    if (!ledgerName) throw new Error("Voucher leg ledgerName is required");
    if (!["Dr", "Cr"].includes(drcr)) throw new Error("Voucher leg drcr must be Dr or Cr");
    if (!Number.isFinite(absAmount) || absAmount <= 0) throw new Error("Voucher leg amount must be > 0");

    const isDeemedPositive = drcr === "Dr" ? "Yes" : "No";
    const signedAmount = drcr === "Dr" ? -absAmount : absAmount;
    signedSum += signedAmount;

    return `<ALLLEDGERENTRIES.LIST><LEDGERNAME>${escapeXml(ledgerName)}</LEDGERNAME><ISDEEMEDPOSITIVE>${isDeemedPositive}</ISDEEMEDPOSITIVE><AMOUNT>${signedAmount.toFixed(2)}</AMOUNT></ALLLEDGERENTRIES.LIST>`;
  }).join("");

  if (Math.abs(signedSum) > 0.01) {
    throw new Error(`Voucher legs do not sum to zero (sum=${signedSum.toFixed(2)})`);
  }

  return `<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY>${escapeXml(company)}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC><REQUESTDATA><TALLYMESSAGE><VOUCHER VCHTYPE="${escapeXml(voucherType)}" ACTION="Create" REMOTEID="${escapeXml(remoteId)}"><DATE>${toTallyDate(date)}</DATE><VOUCHERTYPENAME>${escapeXml(voucherType)}</VOUCHERTYPENAME><NARRATION>${escapeXml(fullNarration)}</NARRATION>${legXml}</VOUCHER></TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>`;
}

async function postVoucherWithRetry(args, voucher) {
  const xml = voucherXml(voucher, args.company);
  let lastResponse = "";
  for (let attempt = 0; attempt < 3; attempt += 1) {
    lastResponse = await postTallyXml(args.tallyUrl, xml);
    const retrySplit = /retry\s+split/i.test(lastResponse);
    if (retrySplit) {
      await sleep(350 + attempt * 200);
      continue;
    }
    const created = parseTagNumber(lastResponse, "CREATED");
    const altered = parseTagNumber(lastResponse, "ALTERED");
    const exceptions = parseTagNumber(lastResponse, "EXCEPTIONS");
    if (created + altered > 0 && exceptions === 0) {
      return { ok: true, message: "Posted", tallyVoucherNumber: "" };
    }
    const lineError = parseLineError(lastResponse);
    return {
      ok: false,
      message: lineError || `Tally import failed (created=${created}, altered=${altered}, exceptions=${exceptions})`,
      tallyVoucherNumber: "",
    };
  }
  const lineError = parseLineError(lastResponse);
  return { ok: false, message: lineError || "Tally asked to retry Split repeatedly", tallyVoucherNumber: "" };
}

async function main() {
  if (typeof fetch !== "function") fail("Node.js 18+ is required (built-in fetch missing)");

  const args = parseArgs(process.argv.slice(2));
  const baseUrl = normalizeEndpointBase(args.endpoint);
  if (!baseUrl) fail("Missing endpoint. Use --endpoint=... or set TALLY_BRIDGE_ENDPOINT");
  if (!args.token.trim()) fail("Missing token. Use --token=... or set TALLY_BRIDGE_TOKEN");

  const pullUrl = `${baseUrl}/api/tally/bridge/vouchers?status=pending`;
  const resultUrl = `${baseUrl}/api/tally/bridge/vouchers/results`;

  console.log(`Pulling pending vouchers from: ${pullUrl}`);
  const pending = await fetchJson(pullUrl, args.token, { timeoutMs: 60000 });
  if (!Array.isArray(pending) || pending.length === 0) {
    console.log("No pending vouchers to post.");
    return;
  }
  console.log(`Found ${pending.length} pending voucher(s)`);

  await ensureLedgersExist(args, pending);

  const results = [];
  let posted = 0;
  let failed = 0;

  for (let index = 0; index < pending.length; index += 1) {
    const voucher = pending[index];
    const queueId = String(voucher._id || "");
    const remoteId = String(voucher.remoteId || "");
    const label = `${index + 1}/${pending.length}`;
    process.stdout.write(`[${label}] Posting ${remoteId || queueId} ... `);
    try {
      const postResult = await postVoucherWithRetry(args, voucher);
      if (postResult.ok) {
        posted += 1;
        process.stdout.write("OK\n");
        results.push({
          queueId,
          status: "posted",
          message: postResult.message,
          tallyVoucherNumber: postResult.tallyVoucherNumber || undefined,
        });
      } else {
        failed += 1;
        process.stdout.write(`FAILED (${postResult.message})\n`);
        results.push({ queueId, status: "failed", message: postResult.message });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      failed += 1;
      process.stdout.write(`FAILED (${message})\n`);
      results.push({ queueId, status: "failed", message });
    }
    await sleep(180);
  }

  console.log(`Reporting ${results.length} result(s) back to backend...`);
  const reportResponse = await fetchJson(resultUrl, args.token, {
    method: "POST",
    body: results,
    timeoutMs: 90000,
  });

  console.log("Done.");
  console.log(JSON.stringify({ posted, failed, backend: reportResponse }, null, 2));
}

main().catch((error) => {
  fail(error instanceof Error ? error.message : String(error));
});
