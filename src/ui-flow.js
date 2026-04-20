export function shouldAttemptPinUnlock(pin, requiredLength) {
  return typeof pin === "string" && typeof requiredLength === "number" && requiredLength >= 4 && requiredLength <= 6 && pin.length === requiredLength;
}

export function buildPinDots(pin, requiredLength) {
  const total = typeof requiredLength === "number" && requiredLength >= 4 ? requiredLength : 4;
  return Array.from({ length: total }, (_, index) => (index < pin.length ? "●" : "○"));
}

export function buildLockoutMessage(authLockedUntil, now = () => Date.now()) {
  if (!authLockedUntil) {
    return null;
  }

  const retryAt = Date.parse(authLockedUntil);
  if (Number.isNaN(retryAt)) {
    return "Authentication is temporarily blocked.";
  }

  const remainingMs = retryAt - now();
  if (remainingMs <= 0) {
    return null;
  }

  return `Too many attempts, try again in ${Math.max(1, Math.ceil(remainingMs / 1000))}s`;
}

export function maskSecret(secret) {
  const length = typeof secret === "string" && secret.length > 0 ? secret.length : 12;
  return "•".repeat(Math.max(8, Math.min(length, 24)));
}

export function normalizeRecordDraft(draft) {
  return {
    key: draft.key.trim(),
    name: draft.name.trim(),
    username: draft.username.trim(),
    secret: draft.secret,
    notes: draft.notes.trim(),
  };
}

export function draftHasRequiredFields(draft) {
  const normalized = normalizeRecordDraft(draft);
  return Boolean(normalized.key && normalized.name && normalized.secret);
}
