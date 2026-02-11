import json
import os
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _set_offline_env() -> None:
    # Some transformers/hf-hub paths still attempt network unless forced offline.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _cosine(a, b) -> float:
    import torch

    a = a.float()
    b = b.float()
    denom = (a.norm(p=2) * b.norm(p=2)).clamp_min(1e-12)
    return float((a @ b) / denom)


def _mean_pool(last_hidden_state, attention_mask):
    import torch

    # last_hidden_state: [B, T, H], attention_mask: [B, T]
    mask = attention_mask.unsqueeze(-1).to(dtype=last_hidden_state.dtype)
    summed = (last_hidden_state * mask).sum(dim=1)
    denom = mask.sum(dim=1).clamp_min(1.0)
    return summed / denom


def _embed_texts(model, tokenizer, texts: list[str], *, device: str, max_length: int, remap: dict[str, int] | None):
    import torch

    enc = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
        add_special_tokens=True,
    )

    input_ids = enc["input_ids"]
    attention_mask = enc.get("attention_mask", None)
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids, dtype=torch.long)

    if remap is not None:
        # Map unknown ids to the new-vocab unk id.
        unk_old = tokenizer.unk_token_id
        if unk_old is None:
            raise RuntimeError("Tokenizer has no unk_token_id; cannot remap for subset model.")
        unk_new = remap.get(str(int(unk_old)))
        if unk_new is None:
            raise RuntimeError("Remap is missing unk id mapping; ensure specials were kept.")

        # This is intentionally simple and correct (tests are small).
        ids = input_ids.cpu().tolist()
        for bi in range(len(ids)):
            ids[bi] = [int(remap.get(str(int(t)), unk_new)) for t in ids[bi]]
        input_ids = torch.tensor(ids, dtype=torch.long)

    input_ids = input_ids.to(device)
    attention_mask = attention_mask.to(device)

    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)

    # Prefer an explicit pooled output when provided; otherwise mean-pool.
    pooled = getattr(out, "pooler_output", None)
    if pooled is None:
        last_hidden = getattr(out, "last_hidden_state", None)
        if last_hidden is None:
            raise RuntimeError("Model output missing pooler_output and last_hidden_state.")
        pooled = _mean_pool(last_hidden, attention_mask)

    pooled = pooled.float()
    pooled = pooled / pooled.norm(p=2, dim=-1, keepdim=True).clamp_min(1e-12)
    return pooled.cpu()


@dataclass(frozen=True)
class ModelSpec:
    base: str
    subset_dir: str | None


class TestEmbeddingGemmaSubsetEmbeddings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _set_offline_env()

        cls.model_spec = ModelSpec(
            base=os.environ.get("EMBEDDINGGEMMA_BASE_MODEL", "google/embeddinggemma-300m"),
            subset_dir=os.environ.get("EMBEDDINGGEMMA_SUBSET_DIR"),
        )
        cls.device = os.environ.get("EMBEDDINGGEMMA_TEST_DEVICE", "cpu")
        cls.max_length = int(os.environ.get("EMBEDDINGGEMMA_TEST_MAX_LEN", "128"))
        cls.subset_langs = None
        langs_env = os.environ.get("EMBEDDINGGEMMA_SUBSET_LANGS")
        if isinstance(langs_env, str) and langs_env.strip():
            cls.subset_langs = [x.strip() for x in langs_env.split(",") if x.strip()]

        try:
            from transformers import AutoModel, AutoTokenizer
        except Exception as e:
            raise unittest.SkipTest(f"transformers not available: {e}")

        # Base tokenizer/model.
        try:
            cls.base_tokenizer = AutoTokenizer.from_pretrained(
                cls.model_spec.base,
                local_files_only=True,
                trust_remote_code=False,
                use_fast=True,
            )
            cls.base_model = AutoModel.from_pretrained(
                cls.model_spec.base,
                local_files_only=True,
                trust_remote_code=False,
                low_cpu_mem_usage=True,
            ).to(cls.device)
            cls.base_model.eval()
        except Exception as e:
            raise unittest.SkipTest(f"Base model not available locally: {e}")

        # Optional subset model.
        cls.subset_model = None
        cls.subset_remap = None
        cls.subset_vocab_size = None
        if cls.model_spec.subset_dir:
            subset_dir = Path(cls.model_spec.subset_dir)
            if not subset_dir.exists():
                raise unittest.SkipTest(f"Subset dir does not exist: {subset_dir}")

            remap_path = subset_dir / "id_remap.json"
            if not remap_path.exists():
                raise unittest.SkipTest(f"Subset remap missing: {remap_path}")

            remap_json = _load_json(remap_path)
            old_to_new = remap_json.get("old_to_new", {})
            if not isinstance(old_to_new, dict) or not old_to_new:
                raise unittest.SkipTest(f"Subset remap is empty: {remap_path}")

            try:
                cls.subset_model = AutoModel.from_pretrained(
                    str(subset_dir),
                    local_files_only=True,
                    trust_remote_code=False,
                    low_cpu_mem_usage=True,
                ).to(cls.device)
                cls.subset_model.eval()
                cls.subset_remap = old_to_new
                cls.subset_vocab_size = int(getattr(cls.subset_model.config, "vocab_size", -1))
            except Exception as e:
                raise unittest.SkipTest(f"Subset model failed to load: {e}")

    def test_base_model_retrieval_sanity(self):
        docs = _load_json(Path(__file__).with_name("documents.json"))
        # Use English only for a minimal sanity check.
        en = docs["en"]
        q = en["queries"][0]
        d_pos = en["docs"][0]
        d_neg = en["docs"][1]

        qv, dv_pos, dv_neg = _embed_texts(
            self.base_model,
            self.base_tokenizer,
            [q, d_pos, d_neg],
            device=self.device,
            max_length=self.max_length,
            remap=None,
        )
        sim_pos = _cosine(qv, dv_pos)
        sim_neg = _cosine(qv, dv_neg)
        self.assertGreater(sim_pos, sim_neg)

    def test_subset_preserves_top1_retrieval(self):
        if self.subset_model is None or self.subset_remap is None:
            raise unittest.SkipTest("Subset model not configured; set EMBEDDINGGEMMA_SUBSET_DIR.")

        docs = _load_json(Path(__file__).with_name("documents.json"))

        # Determine which language bundles to validate for the subset model.
        # If this subset is single-language, set EMBEDDINGGEMMA_SUBSET_LANGS (e.g. "en") or name the subset dir
        # with a "-<tag>-" fragment (e.g. "...-en-vocab50000").
        subset_langs = self.subset_langs
        if subset_langs is None:
            subset_langs = []
            subset_dir = (self.model_spec.subset_dir or "").lower()
            for lang in docs.keys():
                if f"-{lang}-" in subset_dir:
                    subset_langs.append(lang)
            if not subset_langs:
                # Default to English for a single-language subset when unspecified.
                subset_langs = ["en"]

        # For each selected language: assert relevant doc is top-1 for each query in both models.
        for lang in subset_langs:
            bundle = docs.get(lang)
            if bundle is None:
                raise RuntimeError(f"Unknown language tag in subset langs: {lang}")
            queries = bundle["queries"]
            docs_list = bundle["docs"]
            relevant = bundle["relevant"]

            # Pre-embed docs once per model.
            base_doc_vecs = _embed_texts(
                self.base_model,
                self.base_tokenizer,
                docs_list,
                device=self.device,
                max_length=self.max_length,
                remap=None,
            )
            sub_doc_vecs = _embed_texts(
                self.subset_model,
                self.base_tokenizer,
                docs_list,
                device=self.device,
                max_length=self.max_length,
                remap=self.subset_remap,
            )

            for qi, di in relevant:
                q = queries[qi]

                base_qv = _embed_texts(
                    self.base_model,
                    self.base_tokenizer,
                    [q],
                    device=self.device,
                    max_length=self.max_length,
                    remap=None,
                )[0]
                sub_qv = _embed_texts(
                    self.subset_model,
                    self.base_tokenizer,
                    [q],
                    device=self.device,
                    max_length=self.max_length,
                    remap=self.subset_remap,
                )[0]

                # Compute similarities to each doc.
                base_sims = [float((base_qv @ dv).item()) for dv in base_doc_vecs]
                sub_sims = [float((sub_qv @ dv).item()) for dv in sub_doc_vecs]

                base_top = max(range(len(base_sims)), key=lambda i: base_sims[i])
                sub_top = max(range(len(sub_sims)), key=lambda i: sub_sims[i])

                self.assertEqual(base_top, di, msg=f"[{lang}] base top1 mismatch for query {qi}")
                self.assertEqual(sub_top, di, msg=f"[{lang}] subset top1 mismatch for query {qi}")

    def test_subset_remap_stays_in_vocab(self):
        if self.subset_model is None or self.subset_remap is None or self.subset_vocab_size is None:
            raise unittest.SkipTest("Subset model not configured; set EMBEDDINGGEMMA_SUBSET_DIR.")
        if self.subset_vocab_size <= 0:
            raise unittest.SkipTest("Subset model config has no vocab_size.")

        # Check that the mapped special ids are within vocab.
        unk_old = self.base_tokenizer.unk_token_id
        self.assertIsNotNone(unk_old)
        unk_new = self.subset_remap.get(str(int(unk_old)))
        self.assertIsNotNone(unk_new)
        self.assertGreaterEqual(int(unk_new), 0)
        self.assertLess(int(unk_new), int(self.subset_vocab_size))


if __name__ == "__main__":
    unittest.main()
