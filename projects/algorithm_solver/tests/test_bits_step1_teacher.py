import json
import pathlib
import tempfile
import unittest
from subprocess import CompletedProcess
from unittest.mock import patch

from algsolve.synth import bits_step1_teacher as teacher


class TeacherCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.template = self.root / "prompt"
        self.template.write_text("{{PUBLIC_INPUT}}")
        self.config = {"prompt_sha256": teacher.template_sha256(self.template), "model_id": "authorized-model"}

    def call(self, stdout, code=0):
        # make_generate_fn first runs `claude --version`; the second result is the teacher call.
        results = [CompletedProcess([], 0, "v", ""), CompletedProcess([], code, stdout, "")]
        with patch.object(teacher.subprocess, "run", side_effect=results):
            generate, _ = teacher.make_generate_fn(self.template, model="authorized-model", log_path=self.root / "log")
            return generate("uid", {}, "plan", self.config)

    def test_cli_error_reports_the_cli_message(self):
        with self.assertRaisesRegex(RuntimeError, "OAuth session expired"):
            self.call(json.dumps({"is_error": True, "result": "OAuth session expired"}), 1)

    def test_cli_error_with_non_object_body_is_still_a_cli_error(self):
        with self.assertRaisesRegex(RuntimeError, "claude exited 1"):
            self.call("[]", 1)

    def test_invalid_json(self):
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            self.call("not-json")

    def test_empty_output(self):
        with self.assertRaisesRegex(ValueError, "empty or invalid JSON"):
            self.call("")

    def test_non_object_envelope(self):
        with self.assertRaisesRegex(ValueError, "not a JSON object"):
            self.call("[]")

    def test_valid_envelope(self):
        self.assertEqual(self.call(json.dumps({"result": "[]"})), [])


class RecordedTeacherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        template = self.root / "prompt"
        template.write_text("{{PUBLIC_INPUT}}")
        self.config = {"prompt_sha256": teacher.template_sha256(template), "model_id": "authorized-model"}

    def recorded(self, **overrides):
        record = {"uid": "uid", "plan_sha256": "plan", "prompt_sha256": self.config["prompt_sha256"],
                  "public_input_sha256": teacher.public_input_sha256({}), "model": "authorized-model",
                  "proposals": []}
        record.update(overrides)
        record = {key: value for key, value in record.items() if value is not None}
        path = self.root / "record"
        path.write_text(json.dumps(record) + "\n")
        generate, _ = teacher.make_recorded_fn(path)
        return generate

    def test_matching_record_replays(self):
        self.assertEqual(self.recorded()("uid", {}, "plan", self.config), [])

    def test_input_plan_and_prompt_are_bound(self):
        generate = self.recorded()
        for public_input, plan, config in [({"x": 1}, "plan", self.config), ({}, "other", self.config),
                                           ({}, "plan", {**self.config, "prompt_sha256": "other"})]:
            with self.assertRaises(PermissionError):
                generate("uid", public_input, plan, config)

    def test_different_model_is_refused(self):
        with self.assertRaisesRegex(PermissionError, "different model"):
            self.recorded(model="wrong-model")("uid", {}, "plan", self.config)

    def test_record_without_model_is_refused(self):
        with self.assertRaisesRegex(PermissionError, "different model"):
            self.recorded(model=None)("uid", {}, "plan", self.config)

    def test_recorded_failure_is_reported(self):
        with self.assertRaisesRegex(ValueError, "Recorded teacher call failed: boom"):
            self.recorded(error="boom")("uid", {}, "plan", self.config)


if __name__ == "__main__":
    unittest.main()
