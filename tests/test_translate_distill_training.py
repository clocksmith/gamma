"""Focused tests for native-prompt translation knowledge distillation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch


_TRAINER_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "training"
    / "train_translate_distill.py"
)
_SPEC = importlib.util.spec_from_file_location("train_translate_distill", _TRAINER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_TRAINER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _TRAINER
_SPEC.loader.exec_module(_TRAINER)


class TranslateDistillKdAlignmentTests(unittest.TestCase):
    def test_peft_adapter_directory_is_a_valid_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / "checkpoint-000100"
            checkpoint.mkdir()
            (checkpoint / "adapter_config.json").write_text("{}\n", encoding="utf-8")
            (checkpoint / "adapter_model.safetensors").write_bytes(b"adapter")

            self.assertTrue(_TRAINER._is_valid_checkpoint_dir(checkpoint))

    def test_parser_exposes_backward_compatible_sft_weight(self) -> None:
        argv = [
            "train_translate_distill.py",
            "--pairs",
            "pairs.jsonl",
            "--teacher-model",
            "teacher",
            "--student-model",
            "student",
        ]
        with patch.object(sys, "argv", argv):
            args = _TRAINER._parse_args()
        self.assertEqual(args.lambda_sft, 1.0)
        self.assertTrue(args.save_optimizer_state)

    def test_parser_can_disable_optimizer_checkpoint_state(self) -> None:
        argv = [
            "train_translate_distill.py",
            "--pairs",
            "pairs.jsonl",
            "--teacher-model",
            "teacher",
            "--student-model",
            "student",
            "--no-save-optimizer-state",
        ]
        with patch.object(sys, "argv", argv):
            args = _TRAINER._parse_args()
        self.assertFalse(args.save_optimizer_state)

    def test_matching_target_positions_ignore_prompt_length_and_template_tokens(self) -> None:
        student_labels = torch.tensor([[-100, -100, 1, 2, 3, 4]])
        teacher_labels = torch.tensor([[-100, -100, -100, 1, 2, 9, 3, 4]])

        aligned = _TRAINER._matching_target_positions(student_labels, teacher_labels)

        self.assertEqual(aligned, [([1, 2, 3, 4], [2, 3, 5, 6])])

    def test_kd_loss_uses_aligned_target_logits(self) -> None:
        vocab_size = 12
        student_labels = torch.tensor([[-100, -100, 1, 2, 3, 4]])
        teacher_labels = torch.tensor([[-100, -100, -100, 1, 2, 9, 3, 4]])
        student_logits = torch.zeros((1, 6, vocab_size), requires_grad=True)
        teacher_logits = torch.zeros((1, 8, vocab_size))

        aligned = _TRAINER._matching_target_positions(student_labels, teacher_labels)[0]
        for token_idx, (student_pos, teacher_pos) in enumerate(zip(*aligned, strict=True)):
            values = torch.arange(vocab_size, dtype=torch.float32) * float(token_idx + 1)
            student_logits.data[0, student_pos] = values
            teacher_logits[0, teacher_pos] = values

        loss = _TRAINER._kd_loss(
            student_logits,
            teacher_logits,
            student_labels,
            teacher_labels,
            1.0,
        )

        self.assertLess(float(loss.item()), 1e-6)
        loss.backward()
        self.assertIsNotNone(student_logits.grad)

    def test_kd_loss_detects_different_teacher_distribution(self) -> None:
        student_labels = torch.tensor([[-100, 1, 2]])
        teacher_labels = torch.tensor([[-100, -100, 1, 2]])
        student_logits = torch.zeros((1, 3, 4), requires_grad=True)
        teacher_logits = torch.zeros((1, 4, 4))
        teacher_logits[0, 1, 3] = 8.0
        teacher_logits[0, 2, 3] = 8.0

        loss = _TRAINER._kd_loss(
            student_logits,
            teacher_logits,
            student_labels,
            teacher_labels,
            1.0,
        )

        self.assertGreater(float(loss.item()), 0.5)


if __name__ == "__main__":
    unittest.main()
