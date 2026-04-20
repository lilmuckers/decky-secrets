import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../src/index.tsx", import.meta.url), "utf8");

test("session-locked UI includes a visible wrong-pin cue and lock-state wording", () => {
  assert.match(source, /Enter session PIN/);
  assert.match(source, /Wrong PIN/);
  assert.match(source, /Session lock returns here for PIN re-entry\. Restart or full relock requires the master password again\./);
  assert.match(source, /rgba\(200, 48, 48, 0\.25\)/);
});

test("record list keeps copy as default tap and exposes details through a trailing affordance", () => {
  assert.match(source, /Default tap copies the password\./);
  assert.match(source, /aria-label=\{`View details for \$\{record\.name\}`\}/);
  assert.doesNotMatch(source, />Details<\/ButtonItem>/);
});

test("visible UI wording distinguishes session lock from restart or full relock", () => {
  assert.match(source, /restart or full relock requires the master password again/i);
  assert.match(source, />Session lock<\/ButtonItem>/);
});
