#!/usr/bin/env node
/*
 * Regression test for the web build (index.html).
 *
 * 1. Extracts the core JS between the CORE markers in index.html
 *    (the same code the browser runs — no duplicate implementation).
 * 2. Checks calc() against tests/vectors.json, which is generated from the
 *    Python reference implementation (e6_keygen.calc).
 * 3. Checks the tolerant input parsing shared with the Python CLI.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const match = html.match(/\/\* ==CORE-BEGIN== \*\/([\s\S]*?)\/\* ==CORE-END== \*\//);
if (!match) {
  console.error("FAIL: core markers not found in index.html");
  process.exit(1);
}

const api = new Function(
  match[1] + "\nreturn { calc, parseUid, parseMachineCode, looksLikeUid, resolveInput, uidToMachineCode };"
)();

let passed = 0;
let failed = 0;

function check(name, ok, detail) {
  if (ok) {
    passed += 1;
  } else {
    failed += 1;
    console.error("FAIL: " + name + (detail ? "  (" + detail + ")" : ""));
  }
}

/* ---- 1. numeric vectors (Python <-> JS bit-for-bit) ---- */
const vectors = JSON.parse(fs.readFileSync(path.join(__dirname, "vectors.json"), "utf8"));
for (const c of vectors.cases) {
  const r = api.calc(c.mc);
  check(
    "calc(" + c.mc + ")",
    r.e013 === c.e013 && r.e014 === c.e014,
    "got " + r.e013 + "/" + r.e014 + ", want " + c.e013 + "/" + c.e014
  );
}

/* ---- 2. input parsing / word-order detection ---- */
const DEV1 = "43485943 37303808 000E002D"; // 1953915238 -> 2726 / 3958
const DEV2 = "53483643 53303606 003F0037"; // 4653170    -> 3673 / 2913

const cases = [
  [DEV1, 1953915238, 2726, 3958],
  [DEV2, 4653170, 3673, 2913],
  ["ID:53483643 53303606 003F0037A", 4653170, 3673, 2913], // prefix + trailing junk
  ["003F0037 53303606 53483643", 4653170, 3673, 2913],     // low word first
  ["5348364353303606003F0037", 4653170, 3673, 2913],       // 24 continuous hex chars
  ["K 4653170", 4653170, 3673, 2913],                      // screen format
  ["0x470072", 4653170, 3673, 2913],                       // hex machine code
  ["您的机器码为: 4653170", 4653170, 3673, 2913],           // pasted screen text
];

for (const [input, mc, e13, e14] of cases) {
  let out = null;
  try {
    out = api.resolveInput(input);
  } catch (e) {
    out = null;
  }
  check(
    "input " + JSON.stringify(input),
    !!out && out.machineCode === mc && out.res.e013 === e13 && out.res.e014 === e14,
    out ? "got " + out.machineCode + "/" + out.res.e013 + "/" + out.res.e014 : "threw"
  );
}

/* ---- 3. error paths ---- */
let threw = false;
try {
  api.parseUid("1234 5678");
} catch (e) {
  threw = true;
}
check("parseUid rejects fewer than 3 words", threw);

threw = false;
try {
  api.resolveInput("   ");
} catch (e) {
  threw = true;
}
check("resolveInput rejects empty input", threw);

/* ---- summary ---- */
console.log((failed === 0 ? "PASS" : "FAIL") + " — " + passed + " passed, " + failed + " failed");
process.exit(failed === 0 ? 0 : 1);
