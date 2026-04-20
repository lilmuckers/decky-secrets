export type ClipboardWriter = (text: string) => Promise<void>;
export type SchedulerHandle = unknown;
export type Scheduler = (callback: () => void, delayMs: number) => SchedulerHandle;
export type ClearScheduler = (handle: SchedulerHandle) => void;
export type Clock = () => number;

export declare function formatClipboardTimeoutCue(seconds: number): string;
export declare function buildCopyFeedback(
  recordName: string | null | undefined,
  seconds: number,
): {
  title: string;
  detail: string;
  disclaimer: string;
};
export declare function createClipboardSession(args: {
  writeText: ClipboardWriter;
  schedule?: Scheduler;
  clearScheduled?: ClearScheduler;
  now?: Clock;
}): {
  copySecret(args: { secret: string; timeoutSeconds: number }): Promise<number>;
  clearNow(): Promise<void>;
  recheckExpiry(): Promise<boolean>;
  getExpiry(): number | null;
  dispose(): void;
};
