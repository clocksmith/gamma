"""Opt-in objective for the unstarted paired literal-loss experiment.

No caller selects this automatically. Encoder, predictor, codec and decoding stay
unchanged. Positive/negative classes are balanced separately for each example.
"""
import torch
from torch.nn import functional as F
from .typed_predictor import per_example_loss


def balanced_literal_loss(logits, targets):
    """Mean class BCE per example, ignoring -100 and absent classes.

Every supervised bit must be zero or one. An all-masked example contributes
zero; single-class examples use the ordinary mean BCE for that class.
"""
    if logits.shape != targets.shape or logits.ndim < 2:
        raise ValueError('Expected equal batch-first bit shapes')
    if not torch.all((targets == -100) | (targets == 0) | (targets == 1)):
        raise ValueError('Literal labels must be binary or ignored')
    raw = F.binary_cross_entropy_with_logits(logits, targets.clamp_min(0).to(logits.dtype), reduction='none')
    means, present = [], []
    for label in (0, 1):
        mask = targets == label
        count = mask.flatten(1).sum(1)
        means.append((raw * mask).flatten(1).sum(1) / count.clamp_min(1))
        present.append(count > 0)
    return torch.stack(means).sum(0) / torch.stack(present).sum(0).clamp_min(1)


def per_example_balanced_loss(logits, labels):
    """Existing nonliteral heads plus balanced literal loss; no other changes."""
    literal = balanced_literal_loss(logits['bits'], labels['bits'])
    nonliteral = {key: value for key, value in logits.items() if key != 'bits'}
    return literal + (per_example_loss(nonliteral, labels) if nonliteral else 0)
