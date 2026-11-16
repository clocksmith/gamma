"""Unit and contract tests for training-free surprisal-ridge & shared-hyperbasis transforms."""

from pathlib import Path
import sys
import unittest

import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tasks import DOMAINS, build_domain_tasks, score_domain_output
from transforms import (
    derive_prompt_nll_ridge_lora,
    derive_shared_hyperbasis_lora,
    derive_unembed_surprisal_ridge,
    make_random_norm_matched_factors,
    make_zero_factors,
    temporary_lora_hooks,
)


class _ToyMLP(nn.Module):
    def __init__(self, d_h: int, d_ff: int):
        super().__init__()
        self.gate_proj = nn.Linear(d_h, d_ff, bias=False)
        self.up_proj = nn.Linear(d_h, d_ff, bias=False)
        self.down_proj = nn.Linear(d_ff, d_h, bias=False)
        self.act_fn = nn.SiLU()

    def forward(self, x):
        return self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))


class _ToyLayer(nn.Module):
    def __init__(self, d_h: int, d_ff: int):
        super().__init__()
        self.mlp = _ToyMLP(d_h, d_ff)

    def forward(self, x):
        return x + self.mlp(x)


class _ToyInner(nn.Module):
    def __init__(self, vocab: int, d_h: int, d_ff: int, n_layers: int):
        super().__init__()
        self.embed_tokens = nn.Embedding(vocab, d_h)
        self.layers = nn.ModuleList([_ToyLayer(d_h, d_ff) for _ in range(n_layers)])
        self.norm = nn.RMSNorm(d_h)

    def forward(self, input_ids=None, inputs_embeds=None, use_cache=False, return_dict=True):
        x = inputs_embeds if inputs_embeds is not None else self.embed_tokens(input_ids)
        for layer in self.layers:
            x = layer(x)
        x = self.norm(x)
        return type("Out", (), {"last_hidden_state": x, "past_key_values": None})()


class _ToyCausalLM(nn.Module):
    def __init__(self, vocab: int = 64, d_h: int = 32, d_ff: int = 64, n_layers: int = 4):
        super().__init__()
        self.config = type("Cfg", (), {"hidden_size": d_h, "intermediate_size": d_ff})()
        self.model = _ToyInner(vocab, d_h, d_ff, n_layers)
        self.lm_head = nn.Linear(d_h, vocab, bias=False)

    def forward(self, input_ids=None, inputs_embeds=None, use_cache=False, return_dict=True):
        out = self.model(input_ids=input_ids, inputs_embeds=inputs_embeds)
        logits = self.lm_head(out.last_hidden_state)
        return type("LMOut", (), {"logits": logits, "past_key_values": None})()


class SurprisalRidgeTests(unittest.TestCase):
    def test_domain_tasks_and_oracles_isolate_answers_from_context(self):
        tasks = build_domain_tasks(seed=101, count_per_domain=4)
        self.assertEqual(len(tasks), 12)
        self.assertEqual({t["domain"] for t in tasks}, set(DOMAINS))
        for t in tasks:
            # Oracle accepts exact expected and rejects wrong/empty/corrupted completions
            self.assertTrue(score_domain_output(t["domain"], f"  {t['expected']}\n```", t["expected"]))
            self.assertFalse(score_domain_output(t["domain"], "wrong_answer", t["expected"]))
            self.assertFalse(score_domain_output(t["domain"], f"{t['expected']} trailing_words", t["expected"]))
            # For cipher_codebook and state_trace, final synthesized answer string must NOT appear in context_text!
            if t["domain"] in ("cipher_codebook", "state_trace"):
                self.assertNotIn(t["expected"], t["context_text"])

    def test_transforms_preserve_base_weights_and_zero_identity(self):
        torch.manual_seed(7)
        model = _ToyCausalLM().eval()
        ctx = torch.randint(0, 64, (1, 20))
        qry = torch.randint(0, 64, (1, 25))

        orig_weights = [p.clone() for p in model.parameters()]
        with torch.inference_mode():
            base_logits = model(input_ids=qry).logits.clone()

        f1, n1 = derive_unembed_surprisal_ridge(model, ctx, rank=8)
        f2, n2, shared_bytes = derive_shared_hyperbasis_lora(model, ctx, rank=6)
        f3, n3 = derive_prompt_nll_ridge_lora(model, ctx, rank=6)

        # Shared hyperbasis shares exact same U tensor across all 4 layers
        u_ptrs = {u.data_ptr() for u, _ in f2.values()}
        self.assertEqual(len(u_ptrs), 1)
        naive_bytes = sum((u.numel() + v.numel()) * u.element_size() for u, v in f2.values())
        self.assertLess(shared_bytes, naive_bytes)

        # Zero adapter matches base logits exactly
        zf = make_zero_factors(f1)
        with temporary_lora_hooks(model, zf), torch.inference_mode():
            z_logits = model(input_ids=qry).logits
        self.assertLess((z_logits - base_logits).abs().max().item(), 1e-6)

        # Active transform changes logits during hook context and restores exact base logits on exit
        with temporary_lora_hooks(model, f1), torch.inference_mode():
            mod_logits = model(input_ids=qry).logits
        self.assertGreater((mod_logits - base_logits).abs().max().item(), 1e-5)

        with torch.inference_mode():
            after_logits = model(input_ids=qry).logits
        self.assertEqual((after_logits - base_logits).abs().max().item(), 0.0)

        # Random norm-matched factors match target Frobenius norm
        rf = make_random_norm_matched_factors(f3, n3, seed=99, device="cpu")
        for idx, (ur, vr) in rf.items():
            frob = float((ur @ vr).norm().item())
            self.assertAlmostEqual(frob, n3[idx], places=4)

        # Base weights bit-identical throughout
        for p_before, p_after in zip(orig_weights, model.parameters()):
            self.assertEqual((p_before - p_after).abs().max().item(), 0.0)


if __name__ == "__main__":
    unittest.main()
