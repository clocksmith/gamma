"""Optional PyTorch research hooks, never a fused Doppler implementation.

Selected modules must be the MLP down projections. The caller owns module
identity, tokenization, request serialization, cache lifetime and phase order.
All readback/synchronization and this unfused multiply must be charged to timing.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
import weakref
import hashlib
import json
from types import MappingProxyType

from .rule import _gain_values, _span

_OWNERS = weakref.WeakKeyDictionary()


class _HookSession(AbstractContextManager):
    def __init__(self, modules: Mapping[str, object]):
        if not modules or any(not isinstance(name, str) or not name for name in modules) or len({id(module) for module in modules.values()}) != len(modules):
            raise ValueError("selected modules must be nonempty and distinct")
        self.modules = dict(modules)
        self._handles = []
        self._entered = False
        self._closed = False

    def __enter__(self):
        if self._entered or self._closed:
            raise RuntimeError("hook sessions are single-use")
        if any(module in _OWNERS for module in self.modules.values()):
            raise RuntimeError("selected module already belongs to a channel-gain request")
        try:
            for name, module in self.modules.items():
                _OWNERS[module] = self
                self._handles.append(module.register_forward_pre_hook(self._hook(name)))
            self._entered = True
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        for module in self.modules.values():
            if _OWNERS.get(module) is self:
                del _OWNERS[module]
        self._closed = True

    def __exit__(self, *_):
        self.close()
        return False

    @staticmethod
    def _activation(args):
        import torch
        if len(args) != 1 or not isinstance(args[0], torch.Tensor):
            raise ValueError("down projection must receive one activation tensor")
        value = args[0]
        if value.ndim == 3:
            if value.shape[0] != 1:
                raise ValueError("reference hooks require batch size one")
            tokens = value[0]
        elif value.ndim == 2:
            tokens = value
        else:
            raise ValueError("expected [1,tokens,channels] or [tokens,channels]")
        if not tokens.shape[0] or not tokens.shape[1] or not value.is_floating_point():
            raise ValueError("activation tensor must be nonempty floating point")
        return value, tokens


class EnergyCollector(_HookSession):
    """Observe one full base prefill at each down-projection input.

    Result tensors stay on the input device. export() explicitly reads them back.
    Repeated calls fail: streaming/chunked prefills need a separate checked path.
    """
    def __init__(self, modules, *, token_count: int, start: int, stop: int,
                 template_positions: Sequence[int]):
        super().__init__(modules)
        _span(token_count, start, stop, template_positions)
        self.token_count, self.start, self.stop = token_count, start, stop
        self.energies = {}

    def _hook(self, name):
        def capture(_module, args):
            import torch
            _, tokens = self._activation(args)
            if name in self.energies:
                raise RuntimeError("collector requires exactly one full prefill per module")
            if tokens.shape[0] != self.token_count:
                raise ValueError("activation token count differs from the declared full prefill")
            # Reduction is intentionally device-local; export() owns readback.
            with torch.no_grad():
                span = tokens[self.start:self.stop].detach().float()
                self.energies[name] = (span * span).mean(dim=0)
            return None
        return capture

    def export(self) -> dict[str, tuple[float, ...]]:
        if set(self.energies) != set(self.modules):
            raise RuntimeError("not every selected layer completed its prefill")
        values = {name: tuple(energy.cpu().tolist()) for name, energy in self.energies.items()}
        import math
        if any(not math.isfinite(v) or v < 0 for energy in values.values() for v in energy):
            raise ValueError("nonfinite channel energy")
        return values


class GainApplicator(_HookSession):
    """Multiply input to W_down with an immutable gain tuple, never its weights.

    phase='decode' rejects multi-token calls. phase='re-prefill' applies the same
    frozen gains to the prompt and subsequent decoding; no statistics are collected.
    Remove the context before base prefill of another request.
    """
    def __init__(self, modules, gains: Mapping[str, Sequence[float]], *, phase: str):
        super().__init__(modules)
        if set(gains) != set(modules):
            raise ValueError("gains must name exactly the selected modules")
        if phase not in {"decode", "re-prefill"}:
            raise ValueError("phase must be decode or re-prefill")
        self.gains = MappingProxyType({name: _gain_values(values) for name, values in gains.items()})
        self._gain_hash = hashlib.sha256(json.dumps(dict(self.gains), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
        self.phase = phase
        self._device_gains = {}
        self.calls = dict.fromkeys(modules, 0)

    @property
    def gain_hash(self):
        return self._gain_hash

    def _hook(self, name):
        def apply(_module, args):
            import torch
            value, tokens = self._activation(args)
            if self.phase == "decode" and tokens.shape[0] != 1:
                raise ValueError("decode-only gains cannot run on a multi-token prefill")
            if tokens.shape[1] != len(self.gains[name]):
                raise ValueError("gain channel count does not match down-projection input")
            key = (name, value.device, value.dtype)
            if key not in self._device_gains:
                gains = torch.tensor(self.gains[name], device=value.device, dtype=value.dtype)
                if not bool(torch.isfinite(gains).all()) or not bool((gains > 0).all()):
                    raise ValueError("gain state cannot be represented in activation dtype")
                self._device_gains[key] = gains
            self.calls[name] += 1
            return (value * self._device_gains[key],)
        return apply

    def close(self):
        super().close()
        self._device_gains.clear()
