"""CPU regression for keeping individual support lines isolated inside a padded batch."""
import unittest

import torch
from transformers import Qwen3Config, Qwen3ForCausalLM

from batch_capture_v5 import CaptureInput, capture


class BatchCaptureTest(unittest.TestCase):
    @torch.inference_mode()
    def test_ragged_batches_preserve_every_requested_row_and_do_not_leak_between_lines(self):
        torch.manual_seed(7)
        config = Qwen3Config(vocab_size=64, hidden_size=24, intermediate_size=48, num_hidden_layers=2,
                             num_attention_heads=3, num_key_value_heads=1, head_dim=8)
        model = Qwen3ForCausalLM(config).eval()
        lines = [CaptureInput([1, 2, 3], [1, 2]), CaptureInput([8, 7, 6, 5, 4], [1, 3, 4]),
                 CaptureInput([12, 13], [1])]
        zs, hs, serial = capture(model, lines, 1, 0)
        zb, hb, batch = capture(model, lines, 2, 0)
        self.assertEqual((serial["calls"], batch["calls"]), (3, 2))
        self.assertEqual((batch["tokens"], batch["padded_tokens"]), (10, 12))
        self.assertEqual(zb.shape[0], 6)
        torch.testing.assert_close(zb, zs)
        torch.testing.assert_close(hb, hs)

        # Replace every token in the long neighbour and vary the padding ID.
        lines[1] = CaptureInput([20, 21, 22, 23, 24], [1, 3, 4])
        zr, hr, _ = capture(model, lines, 2, 51)
        torch.testing.assert_close(zr[:2], zs[:2])
        torch.testing.assert_close(hr[:2], hs[:2])


if __name__ == "__main__":
    unittest.main()
