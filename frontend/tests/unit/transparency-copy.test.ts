/**
 * PR-09 — transparency copy gates (no test framework required beyond node assert).
 * Run: npx tsx frontend/tests/unit/transparency-copy.test.ts
 * or:  node --import tsx frontend/tests/unit/transparency-copy.test.ts
 *
 * Also mirrored by backend pytest that reads the TS source for word-count/forbidden phrases
 * so CI without tsx still gates the rules.
 */
import assert from "node:assert/strict";

import {
  FORBIDDEN_PHRASES,
  PAGE,
  TOOLTIPS,
  mainBodyPlainText,
  wordCountMainBody,
} from "../../lib/copy/transparency";

function main() {
  const wc = wordCountMainBody();
  assert.ok(wc > 80, `body too short: ${wc}`);
  assert.ok(wc <= 300, `main body must be ≤300 words, got ${wc}`);

  const blob = (mainBodyPlainText() + " " + JSON.stringify(TOOLTIPS)).toLowerCase();
  for (const phrase of FORBIDDEN_PHRASES) {
    assert.ok(!blob.includes(phrase.toLowerCase()), `forbidden phrase present: ${phrase}`);
  }

  assert.ok(PAGE.sections.length >= 4);
  assert.ok(PAGE.footer.toLowerCase().includes("tham khảo"));
  assert.ok(Object.keys(TOOLTIPS).includes("readiness_band"));
  assert.ok(Object.keys(TOOLTIPS).includes("demand_proxy"));

  // Must mention autonomy / two modes / no gender input theme
  const body = mainBodyPlainText().toLowerCase();
  assert.ok(body.includes("explore") || body.includes("launch") || body.includes("khám phá"));
  assert.ok(body.includes("giới tính") || body.includes("không có ô"));
  assert.ok(body.includes("quyết định"));

  console.log(`OK transparency copy: ${wc} words, forbidden-phrase scan clean`);
}

main();
