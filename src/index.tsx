import { callable, definePlugin } from "@decky/api";
import { ButtonItem, PanelSection, PanelSectionRow, TextField, staticClasses } from "@decky/ui";
import { useEffect, useMemo, useState } from "react";
import { FaKey } from "react-icons/fa";

import { buildCopyFeedback, createClipboardSession } from "./clipboard-flow.js";
import { buildLockoutMessage, buildPinDots, maskSecret, normalizeRecordDraft, shouldAttemptPinUnlock } from "./ui-flow.js";

type VaultState = "uninitialized_vault" | "decrypt_required" | "session_locked" | "accessible" | "relocking";

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
  session_pin_length: number | null;
  clipboard_clear_seconds: number;
  clipboard_clear_best_effort: boolean;
  clipboard_clear_disclaimer: string;
};

type RecordSummary = {
  key: string;
  name: string;
  username: string | null;
};

type RecordDetail = {
  key: string;
  name: string;
  username: string | null;
  notes: string;
};

type ClipboardCopyPayload = {
  record_key: string;
  record_name: string;
  secret: string;
  clipboard_clear_seconds: number;
  best_effort_clear: boolean;
  clear_disclaimer: string;
};

type RecordRevealPayload = {
  record_key: string;
  record_name: string;
  secret: string;
};

type CopyFeedback = {
  title: string;
  detail: string;
  disclaimer: string;
};

type RecordDraft = {
  key: string;
  name: string;
  username: string;
  secret: string;
  notes: string;
};

const getStatus = callable<[], RuntimeStatus>("get_status");
const createVault = callable<[string, string], RuntimeStatus>("create_vault");
const unlockWithMasterPassword = callable<[string], RuntimeStatus>("unlock_with_master_password");
const unlockWithPin = callable<[string], RuntimeStatus>("unlock_with_pin");
const lockToPin = callable<[], RuntimeStatus>("lock_to_pin");
const listRecords = callable<[], RecordSummary[]>("list_records");
const getRecordDetail = callable<[string], RecordDetail>("get_record_detail");
const revealRecordSecret = callable<[string], RecordRevealPayload>("reveal_record_secret");
const saveRecord = callable<[string, string, string | null, string, string | null, string | null], RuntimeStatus>("save_record");
const deleteRecord = callable<[string], RuntimeStatus>("delete_record");
const copyRecordSecret = callable<[string], ClipboardCopyPayload>("copy_record_secret");

const emptyDraft = (): RecordDraft => ({ key: "", name: "", username: "", secret: "", notes: "" });

function Content() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null);
  const [records, setRecords] = useState<RecordSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [copyingRecordKey, setCopyingRecordKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<CopyFeedback | null>(null);
  const [search, setSearch] = useState("");
  const [selectedRecordKey, setSelectedRecordKey] = useState<string | null>(null);
  const [selectedRecordDetail, setSelectedRecordDetail] = useState<RecordDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [revealedSecret, setRevealedSecret] = useState<string | null>(null);
  const [pinValue, setPinValue] = useState("");
  const [pinFeedback, setPinFeedback] = useState<string | null>(null);
  const [pinFailureFlash, setPinFailureFlash] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [draft, setDraft] = useState<RecordDraft>(emptyDraft());
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [masterPassword, setMasterPassword] = useState("");
  const [createMasterPassword, setCreateMasterPassword] = useState("");
  const [confirmMasterPassword, setConfirmMasterPassword] = useState("");
  const [createPin, setCreatePin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");

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

  const resetAccessibleView = () => {
    setSelectedRecordKey(null);
    setSelectedRecordDetail(null);
    setRevealedSecret(null);
    setShowForm(false);
    setEditingKey(null);
    setDraft(emptyDraft());
    setConfirmDelete(false);
  };

  const applyStatus = (nextStatus: RuntimeStatus) => {
    setStatus(nextStatus);
    if (nextStatus.vault_state !== "accessible") {
      setRecords([]);
      resetAccessibleView();
    }
  };

  const refresh = async () => {
    setLoading(true);
    setError(null);

    try {
      const nextStatus = await getStatus();
      applyStatus(nextStatus);
      if (nextStatus.vault_state === "accessible") {
        setRecords(await listRecords());
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load plugin state.");
    } finally {
      setLoading(false);
    }
  };

  const refreshRecords = async () => {
    const nextStatus = await getStatus();
    applyStatus(nextStatus);
    if (nextStatus.vault_state === "accessible") {
      setRecords(await listRecords());
    }
  };

  const loadDetail = async (recordKey: string) => {
    setDetailLoading(true);
    setError(null);
    setRevealedSecret(null);
    try {
      const detail = await getRecordDetail(recordKey);
      setSelectedRecordKey(recordKey);
      setSelectedRecordDetail(detail);
      setShowForm(false);
      setEditingKey(null);
      setConfirmDelete(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load record detail.");
      await refresh();
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateVault = async () => {
    if (createMasterPassword !== confirmMasterPassword) {
      setError("Master passwords do not match.");
      return;
    }
    if (createPin !== confirmPin) {
      setError("PIN entries do not match.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const nextStatus = await createVault(createMasterPassword, createPin);
      applyStatus(nextStatus);
      setCreateMasterPassword("");
      setConfirmMasterPassword("");
      setCreatePin("");
      setConfirmPin("");
      await refreshRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Vault creation failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleMasterUnlock = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const nextStatus = await unlockWithMasterPassword(masterPassword);
      applyStatus(nextStatus);
      setMasterPassword("");
      setPinValue("");
      setPinFeedback(null);
      setPinFailureFlash(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Vault unlock failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const tryPinUnlock = async (candidatePin: string) => {
    setSubmitting(true);
    setError(null);
    try {
      const nextStatus = await unlockWithPin(candidatePin);
      setPinValue("");
      setPinFeedback(null);
      setPinFailureFlash(false);
      applyStatus(nextStatus);
      await refreshRecords();
    } catch (err) {
      const message = err instanceof Error ? err.message : "PIN unlock failed.";
      setPinValue("");
      setPinFeedback(message);
      setPinFailureFlash(!message.includes("temporarily blocked"));
      await refresh();
    } finally {
      setSubmitting(false);
    }
  };

  const appendPinDigit = async (digit: string) => {
    if (submitting || !status?.session_pin_length) {
      return;
    }
    const nextPin = `${pinValue}${digit}`.slice(0, status.session_pin_length);
    setPinValue(nextPin);
    setPinFeedback(null);
    setPinFailureFlash(false);
    if (shouldAttemptPinUnlock(nextPin, status.session_pin_length)) {
      await tryPinUnlock(nextPin);
    }
  };

  const removePinDigit = () => {
    if (submitting) {
      return;
    }
    setPinValue((current) => current.slice(0, -1));
    setPinFeedback(null);
    setPinFailureFlash(false);
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
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password copy failed.");
      await refresh();
    } finally {
      setCopyingRecordKey(null);
    }
  };

  const startReveal = async () => {
    if (!selectedRecordKey) {
      return;
    }
    setError(null);
    try {
      const payload = await revealRecordSecret(selectedRecordKey);
      setRevealedSecret(payload.secret);
    } catch (err) {
      setRevealedSecret(null);
      setError(err instanceof Error ? err.message : "Secret reveal failed.");
      await refresh();
    }
  };

  const stopReveal = () => {
    setRevealedSecret(null);
  };

  const beginAdd = () => {
    setShowForm(true);
    setEditingKey(null);
    setDraft(emptyDraft());
    setSelectedRecordKey(null);
    setSelectedRecordDetail(null);
    setConfirmDelete(false);
    setRevealedSecret(null);
  };

  const beginEdit = () => {
    if (!selectedRecordDetail) {
      return;
    }
    setShowForm(true);
    setEditingKey(selectedRecordDetail.key);
    setDraft({
      key: selectedRecordDetail.key,
      name: selectedRecordDetail.name,
      username: selectedRecordDetail.username ?? "",
      secret: "",
      notes: selectedRecordDetail.notes,
    });
    setConfirmDelete(false);
    setRevealedSecret(null);
  };

  const submitDraft = async () => {
    const normalized = normalizeRecordDraft(draft);
    if (!normalized.key || !normalized.name || (!editingKey && !normalized.secret)) {
      setError(editingKey ? "Key and label are required." : "Key, label, and password are required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const nextStatus = await saveRecord(
        normalized.key,
        normalized.name,
        normalized.username || null,
        normalized.secret,
        normalized.notes || null,
        editingKey,
      );
      applyStatus(nextStatus);
      await refreshRecords();
      setShowForm(false);
      setEditingKey(null);
      await loadDetail(normalized.key);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Record save failed.");
      await refresh();
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedRecordKey) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const nextStatus = await deleteRecord(selectedRecordKey);
      applyStatus(nextStatus);
      await refreshRecords();
      resetAccessibleView();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Record delete failed.");
      await refresh();
    } finally {
      setSubmitting(false);
    }
  };

  const handleManualLock = async () => {
    setSubmitting(true);
    setError(null);
    setRevealedSecret(null);
    try {
      const nextStatus = await lockToPin();
      applyStatus(nextStatus);
      setPinValue("");
      setPinFeedback(null);
      setPinFailureFlash(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Vault lock failed.");
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (!pinFailureFlash) {
      return undefined;
    }

    const timeout = window.setTimeout(() => setPinFailureFlash(false), 900);
    return () => window.clearTimeout(timeout);
  }, [pinFailureFlash]);

  useEffect(() => {
    const handleForegroundReentry = () => {
      void clipboardSession.recheckExpiry().catch(() => undefined);
      void refresh();
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        handleForegroundReentry();
      }
    };

    window.addEventListener("focus", handleForegroundReentry);
    window.addEventListener("pageshow", handleForegroundReentry);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("focus", handleForegroundReentry);
      window.removeEventListener("pageshow", handleForegroundReentry);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      clipboardSession.dispose();
    };
  }, [clipboardSession]);

  const filteredRecords = records.filter((record) => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return true;
    }
    return record.name.toLowerCase().includes(query) || record.key.toLowerCase().includes(query) || (record.username ?? "").toLowerCase().includes(query);
  });

  const inlineLockoutMessage = buildLockoutMessage(status?.auth_locked_until ?? null);

  return (
    <>
      <PanelSection title="Decky Secrets">
        <PanelSectionRow>
          <div>
            {loading && "Loading plugin state..."}
            {!loading && error && `Plugin error: ${error}`}
            {!loading && !error && status && (
              <>
                <div><strong>Vault state:</strong> {status.vault_state}</div>
                <div><strong>Clipboard timeout:</strong> {status.clipboard_clear_seconds}s</div>
              </>
            )}
          </div>
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

      {status?.vault_state === "uninitialized_vault" && (
        <PanelSection title="Create vault">
          <PanelSectionRow><div>No vault yet. Secrets stay hidden by default and unlock requires a master password plus a quick session PIN.</div></PanelSectionRow>
          <PanelSectionRow><TextField label="Master password" bIsPassword value={createMasterPassword} onChange={(e: any) => setCreateMasterPassword(e.target.value)} /></PanelSectionRow>
          <PanelSectionRow><TextField label="Confirm master password" bIsPassword value={confirmMasterPassword} onChange={(e: any) => setConfirmMasterPassword(e.target.value)} /></PanelSectionRow>
          <PanelSectionRow><TextField label="PIN (4 to 6 digits)" bIsPassword value={createPin} onChange={(e: any) => setCreatePin(e.target.value.replace(/\D/g, "").slice(0, 6))} /></PanelSectionRow>
          <PanelSectionRow><TextField label="Confirm PIN" bIsPassword value={confirmPin} onChange={(e: any) => setConfirmPin(e.target.value.replace(/\D/g, "").slice(0, 6))} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below" onClick={() => void handleCreateVault()} disabled={submitting}>Create vault</ButtonItem></PanelSectionRow>
        </PanelSection>
      )}

      {status?.vault_state === "decrypt_required" && (
        <PanelSection title="Unlock vault">
          <PanelSectionRow><div>Master password required. PIN unlock works only after the vault has been opened in this plugin session, and restart or full relock requires the master password again.</div></PanelSectionRow>
          <PanelSectionRow><TextField label="Master password" bIsPassword value={masterPassword} onChange={(e: any) => setMasterPassword(e.target.value)} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below" onClick={() => void handleMasterUnlock()} disabled={submitting}>Unlock</ButtonItem></PanelSectionRow>
        </PanelSection>
      )}

      {status?.vault_state === "session_locked" && (
        <PanelSection title="Enter session PIN">
          <PanelSectionRow>
            <div
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: "8px",
                background: pinFailureFlash ? "rgba(200, 48, 48, 0.25)" : "rgba(255, 255, 255, 0.04)",
                border: pinFailureFlash ? "2px solid rgba(255, 96, 96, 0.9)" : "1px solid rgba(255, 255, 255, 0.08)",
                color: pinFailureFlash ? "#ffb3b3" : "inherit",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "20px", marginBottom: "6px" }}>{buildPinDots(pinValue, status.session_pin_length ?? 4).join(" ")}</div>
              <div>{pinFailureFlash ? "Wrong PIN" : `Enter ${status.session_pin_length ?? "4 to 6"} digit PIN. Unlock happens automatically on the final digit.`}</div>
            </div>
          </PanelSectionRow>
          <PanelSectionRow><div>Session lock returns here for PIN re-entry. Restart or full relock requires the master password again.</div></PanelSectionRow>
          <PanelSectionRow><div>{inlineLockoutMessage ?? pinFeedback ?? ""}</div></PanelSectionRow>
          {[ ["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["⌫", "0"] ].map((row, index) => (
            <PanelSectionRow key={`pin-row-${index}`}>
              <div style={{ display: "flex", gap: "8px", width: "100%", opacity: pinFailureFlash ? 0.92 : 1 }}>
                {row.map((value) => (
                  <div key={value} style={{ flex: 1 }}>
                    <ButtonItem
                      layout="below"
                      onClick={() => {
                        if (value === "⌫") {
                          removePinDigit();
                        } else {
                          void appendPinDigit(value);
                        }
                      }}
                      disabled={submitting || Boolean(inlineLockoutMessage)}
                    >
                      {value}
                    </ButtonItem>
                  </div>
                ))}
              </div>
            </PanelSectionRow>
          ))}
        </PanelSection>
      )}

      {status?.vault_state === "accessible" && !showForm && !selectedRecordKey && (
        <PanelSection title="Secrets">
          <PanelSectionRow><TextField label="Search records" value={search} onChange={(e: any) => setSearch(e.target.value)} /></PanelSectionRow>
          <PanelSectionRow>
            <div style={{ display: "flex", gap: "8px", width: "100%" }}>
              <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={beginAdd}>Add record</ButtonItem></div>
              <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={() => void handleManualLock()}>Session lock</ButtonItem></div>
            </div>
          </PanelSectionRow>
          <PanelSectionRow><div>Default tap copies the password. Session lock returns to PIN, while restart or full relock requires the master password again.</div></PanelSectionRow>
          {filteredRecords.length === 0 ? (
            <PanelSectionRow><div>No matching records yet.</div></PanelSectionRow>
          ) : (
            filteredRecords.map((record) => (
              <PanelSectionRow key={record.key}>
                <div style={{ display: "flex", gap: "8px", width: "100%", alignItems: "stretch" }}>
                  <div style={{ flex: 1 }}>
                    <ButtonItem layout="below" onClick={() => void handleCopy(record)} disabled={copyingRecordKey === record.key}>
                      {copyingRecordKey === record.key ? `Copying ${record.name}...` : record.name}
                    </ButtonItem>
                    <div>{record.username ?? "No username"}</div>
                  </div>
                  <button
                    aria-label={`View details for ${record.name}`}
                    title={`View details for ${record.name}`}
                    onClick={() => void loadDetail(record.key)}
                    style={{ minWidth: "52px", padding: "0 12px", borderRadius: "8px" }}
                  >
                    ›
                  </button>
                </div>
              </PanelSectionRow>
            ))
          )}
        </PanelSection>
      )}

      {status?.vault_state === "accessible" && selectedRecordKey && !showForm && (
        <PanelSection title={selectedRecordDetail?.name ?? "Record detail"}>
          {detailLoading || !selectedRecordDetail ? (
            <PanelSectionRow><div>Loading record detail...</div></PanelSectionRow>
          ) : (
            <>
              <PanelSectionRow><div><strong>Label:</strong> {selectedRecordDetail.name}</div></PanelSectionRow>
              <PanelSectionRow><div><strong>Username:</strong> {selectedRecordDetail.username ?? "None"}</div></PanelSectionRow>
              <PanelSectionRow><div><strong>Password:</strong> {revealedSecret ?? maskSecret(revealedSecret ?? "")}</div></PanelSectionRow>
              <PanelSectionRow>
                <button
                  style={{ width: "100%", padding: "12px" }}
                  onMouseDown={() => void startReveal()}
                  onMouseUp={stopReveal}
                  onMouseLeave={stopReveal}
                  onTouchStart={() => void startReveal()}
                  onTouchEnd={stopReveal}
                >
                  Press and hold to reveal
                </button>
              </PanelSectionRow>
              <PanelSectionRow><ButtonItem layout="below" onClick={() => void handleCopy({ key: selectedRecordDetail.key, name: selectedRecordDetail.name, username: selectedRecordDetail.username })}>Copy password</ButtonItem></PanelSectionRow>
              <PanelSectionRow><div><strong>Notes:</strong> {selectedRecordDetail.notes || "No notes"}</div></PanelSectionRow>
              <PanelSectionRow>
                <div style={{ display: "flex", gap: "8px", width: "100%" }}>
                  <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={beginEdit}>Edit</ButtonItem></div>
                  <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={() => setConfirmDelete((current) => !current)}>Delete</ButtonItem></div>
                </div>
              </PanelSectionRow>
              {confirmDelete && (
                <PanelSectionRow><ButtonItem layout="below" onClick={() => void handleDelete()} disabled={submitting}>Confirm delete</ButtonItem></PanelSectionRow>
              )}
              <PanelSectionRow>
                <div style={{ display: "flex", gap: "8px", width: "100%" }}>
                  <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={() => { setSelectedRecordKey(null); setSelectedRecordDetail(null); }}>Back to list</ButtonItem></div>
                  <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={() => void handleManualLock()}>Session lock</ButtonItem></div>
                </div>
              </PanelSectionRow>
            </>
          )}
        </PanelSection>
      )}

      {status?.vault_state === "accessible" && showForm && (
        <PanelSection title={editingKey ? "Edit record" : "Add record"}>
          <PanelSectionRow><TextField label="Key" value={draft.key} onChange={(e: any) => setDraft((current) => ({ ...current, key: e.target.value }))} /></PanelSectionRow>
          <PanelSectionRow><TextField label="Label" value={draft.name} onChange={(e: any) => setDraft((current) => ({ ...current, name: e.target.value }))} /></PanelSectionRow>
          <PanelSectionRow><TextField label="Username" value={draft.username} onChange={(e: any) => setDraft((current) => ({ ...current, username: e.target.value }))} /></PanelSectionRow>
          <PanelSectionRow><TextField label="Password" bIsPassword value={draft.secret} onChange={(e: any) => setDraft((current) => ({ ...current, secret: e.target.value }))} /></PanelSectionRow>
          <PanelSectionRow><TextField label="Notes" value={draft.notes} onChange={(e: any) => setDraft((current) => ({ ...current, notes: e.target.value }))} /></PanelSectionRow>
          <PanelSectionRow>
            <div style={{ display: "flex", gap: "8px", width: "100%" }}>
              <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={() => void submitDraft()} disabled={submitting}>Save</ButtonItem></div>
              <div style={{ flex: 1 }}><ButtonItem layout="below" onClick={() => { setShowForm(false); setEditingKey(null); }}>Cancel</ButtonItem></div>
            </div>
          </PanelSectionRow>
        </PanelSection>
      )}

      {status && (
        <PanelSection title="Implementation notes">
          {status.notes.map((note) => (
            <PanelSectionRow key={note}><div>{note}</div></PanelSectionRow>
          ))}
        </PanelSection>
      )}
    </>
  );
}

export default definePlugin(() => ({
  name: "Decky Secrets",
  titleView: <div className={staticClasses.Title}>Decky Secrets</div>,
  content: <Content />,
  icon: <FaKey />,
}));
