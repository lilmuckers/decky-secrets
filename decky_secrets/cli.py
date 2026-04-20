from __future__ import annotations

import argparse
import getpass
import io
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Sequence

from .auth import AccessStateError, AuthenticationError, AuthenticationLockedError, VaultAuthManager
from .vault import VaultBlobError, VaultFileStore, VaultPayload, _utc_now


class CliError(Exception):
    exit_code = 1


class UsageError(CliError):
    exit_code = 2


class CliArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(f"{self.format_usage().strip()}\n{message}")


class PromptUnavailableError(CliError):
    pass


@dataclass(frozen=True)
class PromptRequest:
    prompt: str
    stdin_reserved: bool


class SecretPrompter:
    def __init__(self) -> None:
        self.requests: list[PromptRequest] = []

    def prompt_secret(self, prompt: str, *, stdin_reserved: bool) -> str:
        self.requests.append(PromptRequest(prompt=prompt, stdin_reserved=stdin_reserved))
        if stdin_reserved:
            tty_path = Path("/dev/tty")
            if tty_path.exists():
                with tty_path.open("r+", encoding="utf-8", buffering=1) as tty:
                    return getpass.getpass(prompt, stream=tty)
            raise PromptUnavailableError("secure interactive prompt unavailable while --secret-stdin is in use")

        if not sys.stdin.isatty():
            raise PromptUnavailableError("secure interactive prompt unavailable")
        return getpass.getpass(prompt)


class VaultCliApp:
    def __init__(
        self,
        *,
        auth: VaultAuthManager | None = None,
        store: VaultFileStore | None = None,
        prompter: SecretPrompter | None = None,
        stdin: IO[str] | None = None,
        stdout: IO[str] | None = None,
        stderr: IO[str] | None = None,
    ) -> None:
        self.store = store or VaultFileStore()
        self.auth = auth or VaultAuthManager(store=self.store)
        self.prompter = prompter or SecretPrompter()
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self._master_password: bytearray | None = None

    def run(self, argv: Sequence[str]) -> int:
        parser = build_parser()
        try:
            args = parser.parse_args(list(argv))
            if not hasattr(args, "handler"):
                parser.print_help(self.stderr)
                return 2
            return int(args.handler(self, args))
        except SystemExit as exc:
            return int(exc.code)
        except UsageError as exc:
            print(str(exc), file=self.stderr)
            return exc.exit_code
        except PromptUnavailableError as exc:
            print(str(exc), file=self.stderr)
            return exc.exit_code
        except AuthenticationLockedError as exc:
            print(str(exc), file=self.stderr)
            return 1
        except (AuthenticationError, AccessStateError, VaultBlobError, CliError) as exc:
            print(str(exc), file=self.stderr)
            return getattr(exc, "exit_code", 1)

    def handle_list(self, args: argparse.Namespace) -> int:
        del args
        self._authenticate(stdin_reserved=False)
        records = self.auth.access_vault(pin=None, caller="cli", operation=lambda payload: [dict(record) for record in payload.records])
        for record in records:
            username = record.get("username") or "-"
            print(f"{record['key']}\t{record['name']}\t{username}", file=self.stdout)
        return 0

    def handle_add(self, args: argparse.Namespace) -> int:
        secret = self._resolve_secret(args)
        self._authenticate(stdin_reserved=args.secret_stdin)
        master_password = self._require_master_password_for_write()

        def operation(payload: VaultPayload) -> list[dict[str, object]]:
            records = [dict(record) for record in payload.records]
            if any(record["key"] == args.key for record in records):
                raise CliError("record key already exists, use update instead")
            timestamp = _utc_now()
            records.append(
                {
                    "key": args.key,
                    "name": args.name,
                    "username": args.username,
                    "secret": secret,
                    "notes": [],
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
            )
            return records

        self._apply_record_mutation(operation=operation, master_password=master_password)
        print(f"Added record {args.key}", file=self.stdout)
        return 0

    def handle_remove(self, args: argparse.Namespace) -> int:
        self._authenticate(stdin_reserved=False)
        master_password = self._require_master_password_for_write()

        def operation(payload: VaultPayload) -> list[dict[str, object]]:
            records = [dict(record) for record in payload.records]
            remaining = [record for record in records if record["key"] != args.key]
            if len(remaining) == len(records):
                raise CliError("record key not found")
            return remaining

        self._apply_record_mutation(operation=operation, master_password=master_password)
        print(f"Removed record {args.key}", file=self.stdout)
        return 0

    def handle_update(self, args: argparse.Namespace) -> int:
        if args.secret is None and not args.secret_stdin and args.username is None:
            raise UsageError("update requires --secret, --secret-stdin, or --username")
        secret = self._resolve_secret(args) if (args.secret is not None or args.secret_stdin) else None
        self._authenticate(stdin_reserved=args.secret_stdin)
        master_password = self._require_master_password_for_write()

        def operation(payload: VaultPayload) -> list[dict[str, object]]:
            records = [dict(record) for record in payload.records]
            updated = False
            timestamp = _utc_now()
            for record in records:
                if record["key"] != args.key:
                    continue
                if secret is not None:
                    record["secret"] = secret
                if args.username is not None:
                    record["username"] = args.username
                record["updated_at"] = timestamp
                updated = True
                break
            if not updated:
                raise CliError("record key not found")
            return records

        self._apply_record_mutation(operation=operation, master_password=master_password)
        print(f"Updated record {args.key}", file=self.stdout)
        return 0

    def _apply_record_mutation(self, *, operation, master_password: str) -> None:
        def mutate(payload: VaultPayload) -> dict:
            updated_records = operation(payload)
            payload.records.clear()
            payload.records.extend(updated_records)
            data = payload.to_dict()
            data["vault"]["updated_at"] = _utc_now()
            return data

        payload_dict = self.auth.access_vault(pin=None, caller="cli", operation=mutate)
        updated_payload = VaultPayload.from_dict(payload_dict)
        self.store.save_vault(updated_payload, master_password=master_password)

    def _authenticate(self, *, stdin_reserved: bool) -> None:
        status = self.auth.get_status()
        if status.state == "uninitialized_vault":
            raise CliError("vault has not been initialized")
        if status.state == "decrypt_required":
            master_password = self.prompter.prompt_secret("Master password: ", stdin_reserved=stdin_reserved)
            self._cache_master_password(master_password)
            status = self.auth.unlock_with_password(master_password=master_password, caller="cli")
        if status.state == "session_locked":
            pin = self.prompter.prompt_secret("PIN: ", stdin_reserved=stdin_reserved)
            self.auth.unlock_with_pin(pin=pin, caller="cli")
        elif status.state != "accessible":
            raise CliError("vault is not available")

    def _cache_master_password(self, master_password: str) -> None:
        if self._master_password is not None:
            for index in range(len(self._master_password)):
                self._master_password[index] = 0
        self._master_password = bytearray(master_password.encode("utf-8"))

    def _require_master_password_for_write(self) -> str:
        if self._master_password is None:
            raise CliError("write operations require a prior master password unlock in this process")
        return self._master_password.decode("utf-8")

    def _resolve_secret(self, args: argparse.Namespace) -> str:
        if args.secret is not None and args.secret_stdin:
            raise UsageError("--secret and --secret-stdin are mutually exclusive")
        if args.secret is None and not args.secret_stdin:
            raise UsageError("a secret is required via --secret or --secret-stdin")
        if args.secret_stdin:
            value = self.stdin.read()
            if value.endswith("\n"):
                value = value[:-1]
            if not value:
                raise UsageError("secret stdin input must not be empty")
            return value
        assert args.secret is not None
        return args.secret


def build_parser() -> argparse.ArgumentParser:
    parser = CliArgumentParser(prog="decky-secrets")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--key", required=True)
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--username")
    add_parser.add_argument("--secret")
    add_parser.add_argument("--secret-stdin", action="store_true")
    add_parser.set_defaults(handler=VaultCliApp.handle_add)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(handler=VaultCliApp.handle_list)

    rm_parser = subparsers.add_parser("rm")
    rm_parser.add_argument("--key", required=True)
    rm_parser.set_defaults(handler=VaultCliApp.handle_remove)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--key", required=True)
    update_parser.add_argument("--secret")
    update_parser.add_argument("--secret-stdin", action="store_true")
    update_parser.add_argument("--username")
    update_parser.set_defaults(handler=VaultCliApp.handle_update)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    app = VaultCliApp()
    return app.run(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
