import { callable, definePlugin } from "@decky/api";
import { ButtonItem, PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { useEffect, useState } from "react";
import { FaKey } from "react-icons/fa";

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
};

const getStatus = callable<[], RuntimeStatus>("get_status");

function Content() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);

    try {
      setStatus(await getStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load plugin status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <>
      <PanelSection title="Decky Secrets scaffold">
        <PanelSectionRow>
          <div>
            {loading && "Loading placeholder plugin state..."}
            {!loading && error && `Backend error: ${error}`}
            {!loading && !error && status && (
              <>
                <div><strong>Plugin:</strong> {status.plugin}</div>
                <div><strong>Version:</strong> {status.version}</div>
                <div><strong>Vault state:</strong> {status.vault_state}</div>
                <div><strong>Backend model:</strong> {status.backend_model}</div>
              </>
            )}
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={() => void refresh()}>
            Refresh scaffold status
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="Reserved MVP screens">
        <PanelSectionRow>
          <div>First run setup, master password unlock, session PIN lock, unlocked record list, and record detail stay intentionally unimplemented in this slice.</div>
        </PanelSectionRow>
      </PanelSection>

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
