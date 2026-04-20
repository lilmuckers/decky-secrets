export function shouldAttemptPinUnlock(pin: string, requiredLength: number | null | undefined): boolean;
export function buildPinDots(pin: string, requiredLength: number | null | undefined): string[];
export function buildLockoutMessage(authLockedUntil: string | null, now?: () => number): string | null;
export function maskSecret(secret?: string | null): string;
export function normalizeRecordDraft(draft: {
  key: string;
  name: string;
  username: string;
  secret: string;
  notes: string;
}): {
  key: string;
  name: string;
  username: string;
  secret: string;
  notes: string;
};
export function draftHasRequiredFields(draft: {
  key: string;
  name: string;
  username: string;
  secret: string;
  notes: string;
}): boolean;
