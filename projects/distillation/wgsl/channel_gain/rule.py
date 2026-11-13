"""Training-free channel gains and matched controls; CPU reference, not a GPU runtime.

Caller supplies frozen settings and exact half-open token spans. Activations are
post-SwiGLU, immediately before W_down. No defaults choose experiment settings.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Sequence, TypeVar

T = TypeVar("T")


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _span(length: int, start: int, stop: int, template_positions: Sequence[int]) -> range:
    if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= length:
        raise ValueError("instruction span must be nonempty and within the token sequence")
    positions = tuple(template_positions)
    if any(type(i) is not int or not 0 <= i < length for i in positions):
        raise ValueError("template positions must be valid token indices")
    if any(start <= i < stop for i in positions):
        raise ValueError("instruction span includes a chat-template token")
    return range(start, stop)


def channel_energy(
    activations: Sequence[Sequence[float]], *, start: int, stop: int,
    template_positions: Sequence[int],
) -> tuple[float, ...]:
    """Mean a**2 over exactly [start, stop); templates are forbidden in that span.

    template_positions is mandatory: the tokenizer/formatter owns its provenance.
    This function never guesses or searches for an instruction in token text.
    """
    indices = _span(len(activations), start, stop, template_positions)
    width = len(activations[start])
    if not width or any(len(activations[i]) != width for i in indices):
        raise ValueError("activation span must be a nonempty rectangular token/channel matrix")
    energy = []
    for channel in range(width):
        squares = []
        for token in indices:
            value = _finite(activations[token][channel], "activation")
            squares.append(_finite(value * value, "squared activation"))
        # Divide each term before summation to avoid overflow of a valid mean.
        energy.append(_finite(math.fsum(v / len(indices) for v in squares), "channel energy"))
    return tuple(energy)


@dataclass(frozen=True)
class GainState:
    """Small immutable per-request state. Re-prefill reuses this exact state."""
    gains: tuple[float, ...]
    log_gains: tuple[float, ...]
    clipped_scores: tuple[float, ...]


def _exponentiate(log_gains: Sequence[float]) -> tuple[float, ...]:
    try:
        gains = tuple(math.exp(_finite(v, "log gain")) for v in log_gains)
    except OverflowError as exc:
        raise ValueError("gain exponentiation overflows") from exc
    if any(not math.isfinite(g) or g <= 0 for g in gains):
        raise ValueError("gains must be finite and strictly positive")
    return gains


def derive_gains(
    instruction_energy: Sequence[float], reference_energy: Sequence[float], *,
    beta: float, clip: float, epsilon: float,
) -> GainState:
    """exp(beta * clip((E_instr-E_ref)/(E_ref+epsilon))) with centered logs.

    The geometric mean is one (within floating point tolerance), not the
    arithmetic mean. Both signs of beta are admitted. Energy cannot be negative.
    """
    beta, clip, epsilon = (_finite(v, n) for v, n in
                           ((beta, "beta"), (clip, "clip"), (epsilon, "epsilon")))
    if clip <= 0 or epsilon <= 0:
        raise ValueError("clip and epsilon must be strictly positive")
    if not instruction_energy or len(instruction_energy) != len(reference_energy):
        raise ValueError("energy vectors must have equal nonzero channel count")
    scores = []
    for instr, ref in zip(instruction_energy, reference_energy):
        instr, ref = _finite(instr, "instruction energy"), _finite(ref, "reference energy")
        if instr < 0 or ref < 0:
            raise ValueError("energy cannot be negative")
        denominator = _finite(ref + epsilon, "reference denominator")
        numerator = instr - ref
        # An overflowed finite ratio saturates at the frozen clip bound. Divide
        # first so subnormal clip*denominator cannot misclassify a zero delta.
        ratio = numerator / denominator
        score = max(-clip, min(clip, ratio))
        scores.append(score)
    logs = tuple(_finite(beta * s, "scaled score") for s in scores)
    mean = math.fsum(v / len(logs) for v in logs)
    centered = tuple(_finite(v - mean, "centered log gain") for v in logs)
    return GainState(_exponentiate(centered), centered, tuple(scores))


def _digest(seed: int, domain: str, index: int) -> bytes:
    if type(seed) is not int:
        raise ValueError("control seed must be an integer")
    return hashlib.sha256(f"channel-gain-v1:{domain}:{seed}:{index}".encode("ascii")).digest()


def permutation(size: int, *, seed: int, domain: str) -> tuple[int, ...]:
    """Portable deterministic hash-order permutation; does not touch global RNG."""
    if type(size) is not int or size < 1:
        raise ValueError("permutation size must be positive")
    if not isinstance(domain, str) or not domain.isascii():
        raise ValueError("permutation domain must be ASCII")
    return tuple(sorted(range(size), key=lambda i: (_digest(seed, domain, i), i)))


def shuffled_context(
    token_ids: Sequence[T], *, start: int, stop: int,
    template_positions: Sequence[int], seed: int,
) -> tuple[T, ...]:
    """Shuffle instruction tokens only, preserving the template and token positions."""
    _span(len(token_ids), start, stop, template_positions)
    order = permutation(stop - start, seed=seed, domain="instruction-tokens")
    return tuple(token_ids[:start]) + tuple(token_ids[start+i] for i in order) + tuple(token_ids[stop:])


def without_instruction(
    token_ids: Sequence[T], *, start: int, stop: int,
    template_positions: Sequence[int],
) -> tuple[T, ...]:
    """Reference A token sequence. Caller must re-prefill; states cannot be sliced."""
    _span(len(token_ids), start, stop, template_positions)
    return tuple(token_ids[:start]) + tuple(token_ids[stop:])


def permuted_gains(gains: Sequence[float], *, seed: int) -> tuple[float, ...]:
    """Same gain multiset, changed channel assignment; no re-normalization."""
    values = _gain_values(gains)
    return tuple(values[i] for i in permutation(len(values), seed=seed, domain="gain-channels"))


def _gain_values(gains: Sequence[float]) -> tuple[float, ...]:
    values = tuple(_finite(g, "gain") for g in gains)
    if not values or any(g <= 0 for g in values):
        raise ValueError("gains must be nonempty and strictly positive")
    return values


def random_gains(gains: Sequence[float], *, seed: int) -> tuple[float, ...]:
    """Random-z control: same dimension and log RMS; no prompt/channel assignment.

    Independent SHA-256-derived uniform[-1,1) values are centered and scaled to
    the supplied state's log RMS. This controls magnitude as well as state size.
    It is distinct from permuting the actual log-gain values.
    """
    values = _gain_values(gains)
    logs = tuple(math.log(g) for g in values)
    target_rms = math.sqrt(math.fsum(v*v / len(logs) for v in logs))
    if target_rms == 0:
        _digest(seed, "random-z", 0)  # Validate the seed even for an identity state.
        return (1.0,) * len(values)
    if len(values) < 2:
        raise ValueError("nonidentity random-z needs at least two channels")
    random = tuple((int.from_bytes(_digest(seed, "random-z", i)[:8], "big") >> 11)
                   / (1 << 53) * 2 - 1 for i in range(len(values)))
    mean = math.fsum(v / len(random) for v in random)
    centered = tuple(v - mean for v in random)
    rms = math.sqrt(math.fsum(v*v / len(centered) for v in centered))
    if rms == 0:
        raise ValueError("degenerate random-z draw")
    return _exponentiate(tuple(v * (target_rms / rms) for v in centered))
