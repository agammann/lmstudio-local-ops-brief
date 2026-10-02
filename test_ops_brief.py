import unittest
import contextlib
import io
import getpass
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from ops_brief import main, post_json, response_content, save_result, validate_brief


class BriefValidationTests(unittest.TestCase):
    def setUp(self):
        self.brief = {
            "reported_facts": ["First response takes about 45 seconds."],
            "unknowns": ["GPU placement has not been checked."],
            "next_checks": ["Inspect the loaded model and runtime state."],
            "priority": "normal",
            "handoff_note": "Capture model-load timing before changing settings.",
        }

    def test_accepts_complete_brief(self):
        self.assertEqual(validate_brief(self.brief), self.brief)

    def test_rejects_invented_field(self):
        self.brief["root_cause"] = "Unknown"
        with self.assertRaises(ValueError):
            validate_brief(self.brief)

    def test_rejects_empty_checks(self):
        self.brief["next_checks"] = []
        with self.assertRaises(ValueError):
            validate_brief(self.brief)

    def test_failed_save_preserves_previous_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "brief.json"
            output.write_text("previous result")
            with patch("ops_brief.os.replace", side_effect=OSError("Fixture write failure")):
                with self.assertRaises(OSError):
                    save_result(output, "replacement")
            self.assertEqual(output.read_text(), "previous result")
            self.assertEqual(list(Path(tmp).iterdir()), [output])

    def test_rejects_unsupported_priority(self):
        self.brief["priority"] = "critical"
        with self.assertRaises(ValueError):
            validate_brief(self.brief)

    def test_rejects_incomplete_but_valid_json(self):
        reply = {"choices": [{"finish_reason": "length", "message": {"content": json.dumps(self.brief)}}]}
        with self.assertRaisesRegex(ValueError, "output limit"):
            response_content(reply, "lmstudio")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "existing.json"
            output.write_text("previous result")
            with patch("sys.argv", ["ops_brief.py", "--model", "fixture", "--output", str(output)]), \
                    patch("ops_brief.post_json", return_value=reply), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 1)
            self.assertEqual(output.read_text(), "previous result")

    def test_hosted_request_uses_visitor_key_fixed_endpoint_and_no_storage(self):
        reply = {"status": "completed", "model": "gpt-5.4", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(self.brief)}]}]}
        out, err = io.StringIO(), io.StringIO()
        with patch("sys.argv", ["ops_brief.py", "--provider", "openai", "--incident", "Exact note."]), \
                patch.dict(os.environ, {"OPENAI_API_KEY": "fixture-visitor-key"}), \
                patch("ops_brief.post_json", return_value=reply) as send, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(main(), 0)
        args, kwargs = send.call_args
        self.assertEqual(args[:2], ("https://api.openai.com", "/v1/responses"))
        self.assertFalse(args[2]["store"])
        self.assertEqual(args[2]["input"][1]["content"], "Exact note.")
        self.assertTrue(args[2]["text"]["format"]["strict"])
        self.assertEqual(kwargs["api_key"], "fixture-visitor-key")
        self.assertNotIn("fixture-visitor-key", out.getvalue() + err.getvalue())
        self.assertEqual(json.loads(out.getvalue())["provider"], "openai")

    def test_missing_or_malformed_hosted_key_makes_no_request(self):
        for key in ("", "secret\ninvalid"):
            with self.subTest(key_present=bool(key)), \
                    patch("sys.argv", ["ops_brief.py", "--provider", "openai"]), \
                    patch.dict(os.environ, {"OPENAI_API_KEY": key}), \
                    patch("sys.stdin.isatty", return_value=False), patch("ops_brief.post_json") as send, \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit) as result:
                    main()
                self.assertEqual(result.exception.code, 2)
                send.assert_not_called()
                self.assertNotIn("secret", err.getvalue())

    def test_empty_and_oversized_notes_make_no_request(self):
        for note in ("  ", "x" * 4001):
            with self.subTest(length=len(note)), \
                    patch("sys.argv", ["ops_brief.py", "--model", "fixture", "--incident", note]), \
                    patch("ops_brief.post_json") as send, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main()
                send.assert_not_called()

    def test_insecure_key_prompt_fails_before_request(self):
        with patch("sys.argv", ["ops_brief.py", "--provider", "openai"]), \
                patch.dict(os.environ, {"OPENAI_API_KEY": ""}), \
                patch("sys.stdin.isatty", return_value=True), \
                patch("ops_brief.getpass.getpass", side_effect=getpass.GetPassWarning), \
                patch("ops_brief.post_json") as send, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                main()
            self.assertEqual(result.exception.code, 2)
            send.assert_not_called()

    def test_rejects_redirect_without_requesting_its_destination(self):
        paths = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                paths.append(self.path)
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(302)
                self.send_header("Location", "/redirected")
                self.end_headers()

            def do_GET(self):
                paths.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with self.assertRaisesRegex(ValueError, "redirects"):
                    post_json(f"http://127.0.0.1:{server.server_port}", "/v1/chat/completions", {})
                self.assertEqual(paths, ["/v1/chat/completions"])
            finally:
                server.shutdown()
                worker.join()

    def test_hosted_incomplete_and_refused_outputs_are_not_saved(self):
        for reply in ({"status": "incomplete"}, {"status": "completed", "output": [
                {"type": "message", "content": [{"type": "refusal", "refusal": "Fixture"}]}]}):
            with self.subTest(reply=reply), self.assertRaises(ValueError):
                response_content(reply, "openai")


if __name__ == "__main__":
    unittest.main()

