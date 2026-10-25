"""Offline encoder only. No index, catalogue approval or recognition decision.

The trusted service owner supplies exact approved artifact manifests. Loading is
lazy; callers retain authority for which public text populations may be encoded.
"""
import importlib.metadata
import os
from pathlib import Path
import sys

from .provision_encoder import pinned, sha

QUERY_INSTRUCTION = 'Instruct: Given a programming problem, retrieve the identical problem\nQuery: '


class PinnedCPUEncoder:
    def __init__(self, model_root, *, encoder_manifest, encoder_manifest_sha256,
                 cpu_manifest, cpu_manifest_sha256, native_python_sha256,
                 threads=2, batch_size=2):
        if type(threads) is not int or threads not in (1, 2):
            raise ValueError('CPU threads must be one or two')
        if type(batch_size) is not int or not 1 <= batch_size <= 4:
            raise ValueError('batch size must be one through four')
        self.model_root = Path(model_root)
        self.encoder_manifest = pinned(encoder_manifest, encoder_manifest_sha256)
        self.cpu_manifest = pinned(cpu_manifest, cpu_manifest_sha256)
        self.encoder_manifest_sha256 = encoder_manifest_sha256
        self.cpu_manifest_sha256 = cpu_manifest_sha256
        self.native_python_sha256 = native_python_sha256
        self.threads, self.batch_size = threads, batch_size
        self._ready = False
        self.last_request_info = None

    def _load(self):
        if self._ready:
            return
        if (sys.version_info[:2] != (3, 13) or
                sha('/usr/bin/python3') != self.native_python_sha256 or
                sha(Path(sys.executable).resolve()) != self.native_python_sha256 or
                Path(sys.prefix).resolve() != (self.model_root.parent / 'venv').resolve()):
            raise ValueError('running Python/private venv identity differs from authorized runtime')
        for row in self.encoder_manifest['files']:
            name = row['path']
            if Path(name).name != name or name in ('', '.', '..'):
                raise ValueError('invalid encoder asset basename')
            path = self.model_root / name
            if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
                raise ValueError('pinned encoder asset changed')
        expected = {name: row['version'] for name, row in self.cpu_manifest['packages'].items()}
        expected['torch'] = self.cpu_manifest['torch']['version']
        if not expected['torch'].endswith('+cpu'):
            raise ValueError('only the pinned CPU torch build is supported')
        if any(importlib.metadata.version(name) != version for name, version in expected.items()):
            raise ValueError('installed package identity differs from pinned CPU runtime')
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                          HF_HOME=str(self.model_root.parent / 'hf-cache'),
                          TORCH_HOME=str(self.model_root.parent / 'torch-cache'), CUDA_VISIBLE_DEVICES='')
        import torch
        from transformers import AutoModel, AutoTokenizer
        self._torch = torch
        torch.set_num_threads(self.threads)
        if torch.get_num_interop_threads() != 1:
            torch.set_num_interop_threads(1)  # An initialized conflicting pool must fail, not be ignored.
        if torch.get_num_interop_threads() != 1:
            raise ValueError('CPU interop thread policy could not be established')
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_root, padding_side='left',
                                                        local_files_only=True, trust_remote_code=False)
        self._model = AutoModel.from_pretrained(self.model_root, dtype=torch.float32,
                                               local_files_only=True, trust_remote_code=False).to('cpu').eval()
        self._ready = True

    @staticmethod
    def prepare_inputs(texts, *, query=False):
        if type(query) is not bool or not isinstance(texts, (list, tuple)) or len(texts) > 64:
            raise ValueError('explicit text batch up to64 rows and boolean query flag required')
        if any(not isinstance(text, str) or not text.strip() or len(text) > 16_384 for text in texts):
            raise ValueError('nonempty public texts up to16384 characters each required')
        return [QUERY_INSTRUCTION + text if query else text for text in texts]

    @staticmethod
    def request_metadata(texts, token_counts, query):
        if len(texts) != len(token_counts) or any(type(n) is not int or n < 0 for n in token_counts):
            raise ValueError('token count metadata is inconsistent')
        return {'rows': len(texts), 'query': query, 'counts_include_query_instruction': query,
                'input_character_counts': [len(text) for text in texts],
                'token_counts_before_truncation': list(token_counts),
                'modeled_token_counts': [min(n, 1024) for n in token_counts],
                'truncated': [n > 1024 for n in token_counts],
                'complete_query_semantics_verified': False}

    def encode(self, texts, *, query=False):
        texts = self.prepare_inputs(texts, query=query)
        self.last_request_info = None
        if not texts:
            self.last_request_info = self.request_metadata([], [], query)
            import numpy as np
            return np.zeros((0, 1024), dtype=np.float32)
        self._load()
        torch = self._torch; result = []
        if torch.get_num_threads() != self.threads or torch.get_num_interop_threads() != 1:
            raise ValueError('CPU thread policy changed after loading')
        raw_tokens = self._tokenizer(texts, padding=False, truncation=False, return_attention_mask=False)['input_ids']
        self.last_request_info = self.request_metadata(texts, [len(ids) for ids in raw_tokens], query)
        for start in range(0, len(texts), self.batch_size):
            encoded = self._tokenizer(texts[start:start + self.batch_size], padding=True,
                                      truncation=True, max_length=1024, return_tensors='pt').to('cpu')
            with torch.no_grad():
                hidden = self._model(**encoded).last_hidden_state
            vectors = torch.nn.functional.normalize(hidden[:, -1].float(), dim=-1)
            if vectors.shape[1] != 1024 or not torch.isfinite(vectors).all():
                raise ValueError('nonfinite or unexpected encoder output')
            result.append(vectors.cpu())
        return torch.cat(result, dim=0).numpy()

    def identity(self):
        return {'schema': 'gamma.offline-cpu-encoder.v1',
                'encoder_manifest_sha256': self.encoder_manifest_sha256,
                'cpu_manifest_sha256': self.cpu_manifest_sha256,
                'native_python_sha256': self.native_python_sha256,
                'adapter_sha256': sha(__file__), 'threads': self.threads, 'interop_threads': 1, 'batch_size': self.batch_size,
                'device': 'cpu', 'dtype': 'float32', 'max_tokens': 1024, 'padding_side': 'left',
                'pooling': 'last-token L2-normalized', 'query_instruction': QUERY_INSTRUCTION,
                'runtime_loaded_and_checked': self._ready,
                'package_check': 'installed versions against verified-wheel manifest; not a fresh installed-file byte audit',
                'old_calibration_reused': False,
                'recognition_qualified': False}
