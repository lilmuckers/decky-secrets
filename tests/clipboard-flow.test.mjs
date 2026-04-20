import test from 'node:test';
import assert from 'node:assert/strict';

import { buildCopyFeedback, createClipboardSession, formatClipboardTimeoutCue } from '../src/clipboard-flow.js';

test('copy feedback never echoes the copied secret value', () => {
  const secret = 'super-secret-password';
  const feedback = buildCopyFeedback('Battle.net', 30);

  assert.equal(feedback.title, 'Password copied for Battle.net');
  assert.equal(feedback.detail, 'Clipboard clears in 30s');
  assert.match(feedback.disclaimer, /Best effort/i);
  assert.doesNotMatch(feedback.title, new RegExp(secret));
  assert.doesNotMatch(feedback.detail, new RegExp(secret));
  assert.doesNotMatch(feedback.disclaimer, new RegExp(secret));
});

test('clipboard session schedules a best-effort clear without retaining the secret in timer state', async () => {
  const writes = [];
  const scheduled = [];
  const clearedHandles = [];
  let nowMs = 1000;
  const session = createClipboardSession({
    writeText: async (text) => {
      writes.push(text);
    },
    schedule: (callback, delayMs) => {
      const handle = { callback, delayMs };
      scheduled.push(handle);
      return handle;
    },
    clearScheduled: (handle) => {
      clearedHandles.push(handle);
    },
    now: () => nowMs,
  });

  const expiresAt = await session.copySecret({ secret: 'super-secret-password', timeoutSeconds: 45 });

  assert.deepEqual(writes, ['super-secret-password']);
  assert.equal(expiresAt, 46000);
  assert.equal(session.getExpiry(), 46000);
  assert.equal(scheduled.length, 1);
  assert.equal(scheduled[0].delayMs, 45000);
  assert.doesNotMatch(String(scheduled[0].callback), /super-secret-password/);

  nowMs = 46000;
  await scheduled[0].callback();
  assert.deepEqual(writes, ['super-secret-password', '']);
  assert.deepEqual(clearedHandles, []);
  assert.equal(session.getExpiry(), null);
});

test('a later copy cancels the earlier clear timer', async () => {
  const writes = [];
  const scheduled = [];
  const clearedHandles = [];
  let nowMs = 0;
  const session = createClipboardSession({
    writeText: async (text) => {
      writes.push(text);
    },
    schedule: (callback, delayMs) => {
      const handle = { callback, delayMs };
      scheduled.push(handle);
      return handle;
    },
    clearScheduled: (handle) => {
      clearedHandles.push(handle);
    },
    now: () => nowMs,
  });

  await session.copySecret({ secret: 'first-secret', timeoutSeconds: 30 });
  nowMs = 5000;
  await session.copySecret({ secret: 'second-secret', timeoutSeconds: 60 });

  assert.deepEqual(writes, ['first-secret', 'second-secret']);
  assert.equal(clearedHandles.length, 1);
  assert.equal(clearedHandles[0], scheduled[0]);

  nowMs = 30000;
  await scheduled[0].callback();
  assert.deepEqual(writes, ['first-secret', 'second-secret']);

  nowMs = 65000;
  await scheduled[1].callback();
  assert.deepEqual(writes, ['first-secret', 'second-secret', '']);
});

test('recheckExpiry clears immediately when real elapsed time exceeded during suspend or backgrounding', async () => {
  const writes = [];
  const scheduled = [];
  let nowMs = 1000;
  const session = createClipboardSession({
    writeText: async (text) => {
      writes.push(text);
    },
    schedule: (callback, delayMs) => {
      const handle = { callback, delayMs };
      scheduled.push(handle);
      return handle;
    },
    now: () => nowMs,
  });

  await session.copySecret({ secret: 'super-secret-password', timeoutSeconds: 30 });
  nowMs = 32050;

  const cleared = await session.recheckExpiry();

  assert.equal(cleared, true);
  assert.deepEqual(writes, ['super-secret-password', '']);
  assert.equal(session.getExpiry(), null);
  assert.equal(scheduled.length, 1);
});

test('recheckExpiry does not clear early before the deadline', async () => {
  const writes = [];
  let nowMs = 1000;
  const session = createClipboardSession({
    writeText: async (text) => {
      writes.push(text);
    },
    schedule: (callback, delayMs) => ({ callback, delayMs }),
    now: () => nowMs,
  });

  await session.copySecret({ secret: 'super-secret-password', timeoutSeconds: 30 });
  nowMs = 15000;

  const cleared = await session.recheckExpiry();

  assert.equal(cleared, false);
  assert.deepEqual(writes, ['super-secret-password']);
  assert.equal(session.getExpiry(), 31000);
});

test('formatClipboardTimeoutCue shows the visible timeout cue', () => {
  assert.equal(formatClipboardTimeoutCue(15), 'Clipboard clears in 15s');
});
