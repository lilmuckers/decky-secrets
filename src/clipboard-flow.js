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

export function createClipboardSession({ writeText, schedule = setTimeout, clearScheduled = clearTimeout }) {
  let currentToken = 0;
  let pendingHandle = null;

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
    await writeText("");
    pendingHandle = null;
    return true;
  };

  return {
    async copySecret({ secret, timeoutSeconds }) {
      currentToken += 1;
      const token = currentToken;
      cancelPending();
      await writeText(secret);
      pendingHandle = schedule(() => {
        void clearClipboardIfCurrent(token);
      }, timeoutSeconds * 1000);
    },
    async clearNow() {
      currentToken += 1;
      cancelPending();
      await writeText("");
    },
    dispose() {
      currentToken += 1;
      cancelPending();
    },
  };
}
