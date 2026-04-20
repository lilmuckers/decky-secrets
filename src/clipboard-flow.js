const DEFAULT_BEST_EFFORT_DETAIL =
  "Best effort only. Clipboard history, pasted destinations, crashes, or restarts may still retain the copied value.";

export function formatClipboardTimeoutCue(seconds) {
  return `Clipboard clears in ${seconds}s`;
}

export function buildCopyFeedback(recordName, seconds) {
  return {
    title: recordName ? `Password copied for ${recordName}` : "Password copied",
    detail: formatClipboardTimeoutCue(seconds),
    disclaimer: DEFAULT_BEST_EFFORT_DETAIL,
  };
}

export function createClipboardSession({
  writeText,
  schedule = setTimeout,
  clearScheduled = clearTimeout,
  now = Date.now,
}) {
  let currentToken = 0;
  let pendingHandle = null;
  let expiresAt = null;

  const cancelPending = () => {
    if (pendingHandle !== null) {
      clearScheduled(pendingHandle);
      pendingHandle = null;
    }
  };

  const clearClipboardIfCurrent = async (token) => {
    if (token !== currentToken) {
      return false;
    }
    expiresAt = null;
    await writeText("");
    pendingHandle = null;
    return true;
  };

  const clearIfExpired = async () => {
    if (expiresAt === null) {
      return false;
    }
    if (now() < expiresAt) {
      return false;
    }
    return clearClipboardIfCurrent(currentToken);
  };

  return {
    async copySecret({ secret, timeoutSeconds }) {
      currentToken += 1;
      const token = currentToken;
      cancelPending();
      await writeText(secret);
      expiresAt = now() + timeoutSeconds * 1000;
      pendingHandle = schedule(() => {
        void clearIfExpired();
      }, timeoutSeconds * 1000);
      return expiresAt;
    },
    async clearNow() {
      currentToken += 1;
      expiresAt = null;
      cancelPending();
      await writeText("");
    },
    async recheckExpiry() {
      return clearIfExpired();
    },
    getExpiry() {
      return expiresAt;
    },
    dispose() {
      currentToken += 1;
      expiresAt = null;
      cancelPending();
    },
  };
}
