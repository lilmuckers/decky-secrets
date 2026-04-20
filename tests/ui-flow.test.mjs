import test from "node:test";
import assert from "node:assert/strict";

import {
  buildLockoutMessage,
  buildPinDots,
  draftHasRequiredFields,
  maskSecret,
  normalizeRecordDraft,
  shouldAttemptPinUnlock,
} from "../src/ui-flow.js";

test("shouldAttemptPinUnlock waits for the configured pin length", () => {
  assert.equal(shouldAttemptPinUnlock("123", 4), false);
  assert.equal(shouldAttemptPinUnlock("1234", 4), true);
  assert.equal(shouldAttemptPinUnlock("12345", 6), false);
  assert.equal(shouldAttemptPinUnlock("123456", 6), true);
});

test("buildPinDots reflects entered digits without exposing the digits themselves", () => {
  assert.deepEqual(buildPinDots("12", 4), ["●", "●", "○", "○"]);
  assert.deepEqual(buildPinDots("12345", 6), ["●", "●", "●", "●", "●", "○"]);
});

test("buildLockoutMessage shows remaining lockout time inline", () => {
  const now = Date.parse("2026-04-20T10:00:00Z");
  assert.equal(
    buildLockoutMessage("2026-04-20T10:00:12Z", () => now),
    "Too many attempts, try again in 12s",
  );
  assert.equal(buildLockoutMessage("2026-04-20T09:59:59Z", () => now), null);
});

test("maskSecret keeps routine detail rendering masked by default", () => {
  assert.equal(maskSecret("hunter2"), "••••••••");
  assert.equal(maskSecret("very-long-secret-value"), "••••••••••••••••••••••");
});

test("normalizeRecordDraft trims non-secret fields without mutating the secret", () => {
  assert.deepEqual(
    normalizeRecordDraft({
      key: " battle-net ",
      name: " Battle.net ",
      username: " player123 ",
      secret: "  keep spacing  ",
      notes: " note one \n note two ",
    }),
    {
      key: "battle-net",
      name: "Battle.net",
      username: "player123",
      secret: "  keep spacing  ",
      notes: "note one \n note two",
    },
  );
});

test("draftHasRequiredFields requires key, name, and secret", () => {
  assert.equal(draftHasRequiredFields({ key: "", name: "Name", username: "", secret: "pw", notes: "" }), false);
  assert.equal(draftHasRequiredFields({ key: "key", name: "", username: "", secret: "pw", notes: "" }), false);
  assert.equal(draftHasRequiredFields({ key: "key", name: "Name", username: "", secret: "", notes: "" }), false);
  assert.equal(draftHasRequiredFields({ key: "key", name: "Name", username: "", secret: "pw", notes: "" }), true);
});
