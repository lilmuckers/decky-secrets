import io
import tempfile
import unittest
from pathlib import Path

from decky_secrets.auth import AuthenticationError, VaultAuthManager
from decky_secrets.cli import PromptRequest, PromptUnavailableError, VaultCliApp
from decky_secrets.vault import VaultFileStore


class FakePrompter:
    def __init__(self, responses: list[str] | None = None, *, error: Exception | None = None) -> None:
        self.responses = list(responses or [])
        self.error = error
        self.requests: list[PromptRequest] = []

    def prompt_secret(self, prompt: str, *, stdin_reserved: bool) -> str:
        self.requests.append(PromptRequest(prompt=prompt, stdin_reserved=stdin_reserved))
        if self.error is not None:
            raise self.error
        if not self.responses:
            raise AssertionError(f"unexpected prompt: {prompt}")
        return self.responses.pop(0)


class VaultCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.home = Path(self.temp_dir.name)
        self.store = VaultFileStore(home_dir=self.home)
        self.store.create_vault(
            master_password="correct horse battery staple",
            pin="1234",
            records=[
                {
                    "key": "battle-net",
                    "name": "Battle.net",
                    "username": "player123",
                    "secret": "super-secret-password",
                    "notes": [],
                }
            ],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _make_app(
        self,
        *,
        responses: list[str] | None = None,
        stdin_text: str = "",
        auth: VaultAuthManager | None = None,
        prompter: FakePrompter | None = None,
    ) -> tuple[VaultCliApp, io.StringIO, io.StringIO]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        app = VaultCliApp(
            auth=auth or VaultAuthManager(store=self.store),
            store=self.store,
            prompter=prompter or FakePrompter(responses),
            stdin=io.StringIO(stdin_text),
            stdout=stdout,
            stderr=stderr,
        )
        return app, stdout, stderr

    def test_list_requires_password_then_pin_and_hides_secret_values(self) -> None:
        app, stdout, stderr = self._make_app(responses=["correct horse battery staple", "1234"])

        exit_code = app.run(["list"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("battle-net\tBattle.net\tplayer123", stdout.getvalue())
        self.assertNotIn("super-secret-password", stdout.getvalue())
        self.assertEqual([request.prompt for request in app.prompter.requests], ["Master password: ", "PIN: "])

    def test_add_supports_secret_stdin_and_preserves_prompt_source(self) -> None:
        app, stdout, stderr = self._make_app(
            responses=["correct horse battery staple", "1234"],
            stdin_text="stdin-secret\n",
        )

        exit_code = app.run(["add", "--key", "wifi", "--name", "Wi-Fi", "--secret-stdin", "--username", "deck"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Added record wifi", stdout.getvalue())
        self.assertTrue(all(request.stdin_reserved for request in app.prompter.requests))

        payload = self.store.load_vault(master_password="correct horse battery staple")
        added = next(record for record in payload.records if record["key"] == "wifi")
        self.assertEqual(added["name"], "Wi-Fi")
        self.assertEqual(added["username"], "deck")
        self.assertEqual(added["secret"], "stdin-secret")

    def test_add_rejects_duplicate_key(self) -> None:
        app, stdout, stderr = self._make_app(responses=["correct horse battery staple", "1234"])

        exit_code = app.run(["add", "--key", "battle-net", "--name", "Duplicate", "--secret", "new-secret"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("record key already exists, use update instead", stderr.getvalue())
        self.assertNotIn("new-secret", stderr.getvalue())

    def test_update_changes_secret_and_username(self) -> None:
        app, stdout, stderr = self._make_app(responses=["correct horse battery staple", "1234"])

        exit_code = app.run(["update", "--key", "battle-net", "--secret", "rotated-secret", "--username", "new-user"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Updated record battle-net", stdout.getvalue())

        payload = self.store.load_vault(master_password="correct horse battery staple")
        updated = next(record for record in payload.records if record["key"] == "battle-net")
        self.assertEqual(updated["secret"], "rotated-secret")
        self.assertEqual(updated["username"], "new-user")

    def test_remove_deletes_record(self) -> None:
        app, stdout, stderr = self._make_app(responses=["correct horse battery staple", "1234"])

        exit_code = app.run(["rm", "--key", "battle-net"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Removed record battle-net", stdout.getvalue())
        payload = self.store.load_vault(master_password="correct horse battery staple")
        self.assertEqual(payload.records, [])

    def test_conflicting_secret_flags_fail_with_nonzero_exit(self) -> None:
        app, stdout, stderr = self._make_app()

        exit_code = app.run(["add", "--key", "wifi", "--name", "Wi-Fi", "--secret", "x", "--secret-stdin"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("mutually exclusive", stderr.getvalue())

    def test_missing_required_arguments_return_help_exit(self) -> None:
        app, stdout, stderr = self._make_app()

        exit_code = app.run(["add", "--key", "wifi"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("usage:", stderr.getvalue())

    def test_one_shot_cli_process_requires_master_password_then_pin(self) -> None:
        app, stdout, stderr = self._make_app(responses=["correct horse battery staple", "1234"])

        exit_code = app.run(["list"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual([request.prompt for request in app.prompter.requests], ["Master password: ", "PIN: "])
        self.assertIn("battle-net\tBattle.net\tplayer123", stdout.getvalue())

    def test_auth_failures_flow_through_shared_lockout(self) -> None:
        auth = VaultAuthManager(store=self.store)
        app, stdout, stderr = self._make_app(responses=["wrong password"] * 5 + ["correct horse battery staple"], auth=auth)

        for _ in range(5):
            self.assertEqual(app.run(["list"]), 1)

        self.assertEqual(app.run(["list"]), 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("authentication temporarily blocked", stderr.getvalue())

    def test_secure_prompt_failure_is_clear_when_secret_stdin_uses_stdin(self) -> None:
        prompter = FakePrompter(error=PromptUnavailableError("secure interactive prompt unavailable while --secret-stdin is in use"))
        app, stdout, stderr = self._make_app(prompter=prompter, stdin_text="stdin-secret\n")

        exit_code = app.run(["add", "--key", "wifi", "--name", "Wi-Fi", "--secret-stdin"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("secure interactive prompt unavailable", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
