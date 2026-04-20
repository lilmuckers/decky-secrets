import { callable, definePlugin } from "@decky/api";
import { ButtonItem, PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { useEffect, useMemo, useState } from "react";
import { FaKey } from "react-icons/fa";

import { buildCopyFeedback, createClipboardSession } from "./clipboard-flow.js";

type VaultState =
  | "uninitialized_vault"
  | "decrypt_required"
  | "session_locked"
  | "accessible"
  | "relocking";

type RuntimeStatus = {
  plugin: string;
  version: string;
  vault_state: VaultState;
  backend_model: string;
  notes: string[];
  vault_path: string;
  vault_exists: boolean;
  auth_locked_until: string | null;
  session_access_expires_at: string | null;
  full_relock_at: string | null;
  clipboard_clear_seconds: number;
  clipboard_clear_best_effort: boolean;
  clipboard_clear_disclaimer: string;
};

type RecordSummary = {
  key: string;
  name: string;
  username: string | null;
};

type ClipboardCopyPayload = {
  record_key: string;
  record_name: string;
  secret: string;
  clipboard_clear_seconds: number;
  best_effort_clear: boolean;
  clear_disclaimer: string;
};

type CopyFeedback = {
  title: string;
  detail: string;
  disclaimer: string;
};

const getStatus = callable<[], RuntimeStatus>("get_status");
const listRecords = callable<[], RecordSummary[]>("list_records");
const copyRecordSecret = callable<[string], ClipboardCopyPayload>("copy_record_secret");

function Content() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null);
  const [records, setRecords] = useState<RecordSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [copyingRecordKey, setCopyingRecordKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<CopyFeedback | null>(null);

  const clipboardSession = useMemo(
    () =>
      createClipboardSession({
        writeText: async (text: string) => {
          if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
            throw new Error("Clipboard API is unavailable in this Decky runtime.");
          }
          await navigator.clipboard.writeText(text);
        },
      }),
    [],
  );

  const refresh = async () => {
    setLoading(true);
    setError(null);

    try {
      const nextStatus = await getStatus();
      setStatus(nextStatus);

      if (nextStatus.vault_state === "accessible") {
        setRecords(await listRecords());
      } else {
        setRecords([]);
        if (copyFeedback) {
          void clipboardSession.clearNow().catch(() => undefined);
        }
        setCopyFeedback(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load plugin state.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (record: RecordSummary) => {
    setCopyingRecordKey(record.key);
    setError(null);

    try {
      const payload = await copyRecordSecret(record.key);
      await clipboardSession.copySecret({
        secret: payload.secret,
        timeoutSeconds: payload.clipboard_clear_seconds,
      });
      setCopyFeedback(buildCopyFeedback(payload.record_name, payload.clipboard_clear_seconds));
      const nextStatus = await getStatus();
      setStatus(nextStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password copy failed.");
    } finally {
      setCopyingRecordKey(null);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    return () => {
      clipboardSession.dispose();
    };
  }, [clipboardSession]);

  return (
    <>
      <PanelSection title="Decky Secrets">
        <PanelSectionRow>
          <div>
            {loading && "Loading plugin state..."}
            {!loading && error && `Plugin error: ${error}`}
            {!loading && !error && status && (
              <>
                <div><strong>Plugin:</strong> {status.plugin}</div>
                <div><strong>Version:</strong> {status.version}</div>
                <div><strong>Vault state:</strong> {status.vault_state}</div>
                <div><strong>Clipboard timeout:</strong> {status.clipboard_clear_seconds}s</div>
              </>
            )}
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={() => void refresh()}>
            Refresh plugin status
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      {copyFeedback && (
        <PanelSection title="Copy confirmation">
          <PanelSectionRow>
            <div>
              <div><strong>{copyFeedback.title}</strong></div>
              <div>{copyFeedback.detail}</div>
              <div>{copyFeedback.disclaimer}</div>
            </div>
          </PanelSectionRow>
        </PanelSection>
      )}

      {status?.vault_state === "accessible" ? (
        <PanelSection title="Unlocked record list">
          {records.length === 0 ? (
            <PanelSectionRow>
              <div>No records are available yet. Copy flow is ready once records exist in the vault.</div>
            </PanelSectionRow>
          ) : (
            records.map((record) => (
              <PanelSectionRow key={record.key}>
                <div style={{ width: "100%" }}>
                  <ButtonItem
                    layout="below"
                    onClick={() => void handleCopy(record)}
                    disabled={copyingRecordKey === record.key}
                  >
                    {copyingRecordKey === record.key ? `Copying ${record.name}...` : `Copy password: ${record.name}`}
                  </ButtonItem>
                  <div>{record.username ?? "No username"}</div>
                  <ButtonItem layout="below" disabled>
                    View details (reserved for issue #9)
                  </ButtonItem>
                  <ButtonItem layout="below" disabled>
                    Edit record (reserved for issue #9)
                  </ButtonItem>
                  <ButtonItem layout="below" disabled>
                    Delete record (reserved for issue #9)
                  </ButtonItem>
                </div>
              </PanelSectionRow>
            ))
          )}
        </PanelSection>
      ) : (
        <PanelSection title="Clipboard gate state">
          <PanelSectionRow>
            <div>
              Fresh copy actions stay blocked until the backend auth state returns to <strong>accessible</strong>.
            </div>
          </PanelSectionRow>
        </PanelSection>
      )}

      {status && (
        <PanelSection title="Implementation notes">
          {status.notes.map((note) => (
            <PanelSectionRow key={note}>
              <div>{note}</div>
            </PanelSectionRow>
          ))}
        </PanelSection>
      )}
    </>
  );
}

export default definePlugin(() => {
  return {
    name: "Decky Secrets",
    titleView: <div className={staticClasses.Title}>Decky Secrets</div>,
    content: <Content />,
    icon: <FaKey />,
  };
});
