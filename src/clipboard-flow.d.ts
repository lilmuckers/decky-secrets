export type ClipboardWriter = (text: string) => Promise<void>;
export type SchedulerHandle = unknown;
export type Scheduler = (callback: () => void, delayMs: number) => SchedulerHandle;
export type ClearScheduler = (handle: SchedulerHandle) => void;

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
}): {
  copySecret(args: { secret: string; timeoutSeconds: number }): Promise<void>;
  clearNow(): Promise<void>;
  dispose(): void;
};
