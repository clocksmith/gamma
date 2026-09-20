"""Trainable title conditioning using the existing normalized token embeddings.

The caller supplies native causal features for each input token. This class
owns no corpus, checkpoint discovery or launch policy. The CPU reference is a
training surrogate; native arithmetic and changed trajectories require replay.
"""
from __future__ import annotations
import importlib


def conditioning(model, package):
    import torch
    reference = importlib.import_module(package + '.model')
    rms_norm = reference.rms_norm
    initialize_scales = reference.InitializeScales(None, None)

    class TitleConditioning(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.base = model
            self.gain = torch.nn.Parameter(torch.zeros(model.cfg.d_model))

        def compute_logits(self, inputs, prior, bounds, counts):
            if counts.shape != (*inputs.shape, 205) or (counts < 0).any() or (counts.sum(-1) > 128).any():
                raise ValueError('invalid title feature geometry')
            embedded = rms_norm(self.base.embedding(torch.arange(205).reshape(1, -1), initialize_scales=initialize_scales))[0]
            # Ascending-symbol accumulation parallels the native construction;
            # native normalized embeddings and downstream arithmetic still
            # differ from this differentiable CPU reference.
            context = counts.new_zeros((*inputs.shape, self.base.cfg.d_model))
            for token in range(205):
                context = context + counts[..., token:token + 1] * embedded[token]
            context = context / counts.sum(-1, keepdim=True).clamp(min=1)
            delta = context * self.gain
            def before_block(_module, args):
                return (args[0] + delta, *args[1:])
            hook = self.base.blocks[0].register_forward_pre_hook(before_block)
            try:
                return self.base.compute_logits(inputs, prior, bounds)
            finally:
                hook.remove()

    return TitleConditioning()


def metadata_entries(gain, mode):
    import numpy as np
    if mode not in (1, 2):
        raise ValueError('metadata mode must be aligned or previous-title')
    values = np.asarray(gain, dtype='<f4')
    if values.shape != (192,) or not np.isfinite(values).all():
        raise ValueError('invalid metadata gain')
    return [('gamma.metadata_gain', 2, values),
            ('gamma.metadata_mode', 3, np.array([mode], dtype='<i4'))]


def validate_features(path, row_count):
    import numpy as np
    if path.stat().st_size != row_count * 411:
        raise ValueError('title feature population differs')
    rows = np.memmap(path, mode='r', dtype=np.uint8, shape=(row_count, 411))
    for start in range(0, row_count, 4096):
        block = rows[start:start + 4096]
        if (block[:, 0] > 128).any() or ((block[:, 0] != 0) & (block[:, 0] < 3)).any():
            raise ValueError('title capacity differs')
        if not np.array_equal(block[:, 1:206].sum(1), block[:, 0]) or not np.array_equal(block[:, 206:].sum(1), block[:, 0]):
            raise ValueError('unmatched title opportunities')
    return rows
