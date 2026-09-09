"""Causal context acquisition for the preserved HARM edit core; no codec claim."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zlib

SOURCE = Path(__file__).resolve().parents[1] / 'programs/harm_route_edit_residual_shadow_q0_v1/core.py'
SOURCE_SHA256 = 'cc03d407d176d64abc1d92be3ec79ce45a56c2c65d8c08d48a93ee81c39233d0'
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
    raise ValueError('preserved HARM core identity differs')
spec = importlib.util.spec_from_file_location('_context_edit_harm_core_v1', SOURCE)
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)

SLOTS, CONTEXT, DONOR, EPISODE = 4096, 8, 32, 32


class Continuation:
    """One predict/observe pair per byte; truth is never passed to predict.

    Histograms are exact positive integer masses, not normalized floats.
    A source position denotes the donor start in this adapter's byte coordinate.
    Source bytes have all been observed before an episode may start.
    """
    def __init__(self, frontend):
        if frontend not in ('synthetic-raw-byte-v1', 'wrt-byte-v1'):
            raise ValueError('an explicit supported byte frontend is required')
        self.frontend = frontend
        self.bank = [None] * SLOTS
        self.tail = bytearray()
        self.position = 0
        self.pending = False
        self.active = None
        self.steps = 0
        self.source_start = None
        self.triggers = 0

    @staticmethod
    def slot(key):
        return zlib.crc32(key) & (SLOTS - 1)

    def predict(self):
        if self.pending:
            raise ValueError('observe the byte before predicting again')
        if self.active is None and len(self.tail) >= CONTEXT:
            key = bytes(self.tail[-CONTEXT:])
            row = self.bank[self.slot(key)]
            if row is not None and row[0] == key:
                _, donor, source_start = row
                if source_start + DONOR > self.position:
                    raise ValueError('donor is not fully observed')
                self.active = dict(L=core.LockstepTransducer(donor),
                                   D=core.EditTransducer(donor),
                                   S=core.EditTransducer(donor[16:] + donor[:16]))
                self.steps = 0
                self.source_start = source_start
                self.triggers += 1
        self.pending = True
        return {arm: None if self.active is None else self.active[arm].histogram()
                for arm in ('L', 'D', 'S')}

    def observe(self, decoded_byte):
        if not self.pending:
            raise ValueError('predict must precede observe')
        if type(decoded_byte) is not int or not 0 <= decoded_byte <= 255:
            raise ValueError('truth must be one byte')
        if self.active is not None:
            for model in self.active.values():
                model.observe(decoded_byte)
            self.steps += 1
            if self.steps == EPISODE:
                self.active = None
                self.source_start = None
        self.position += 1
        self.tail.append(decoded_byte)
        if len(self.tail) > CONTEXT + DONOR:
            del self.tail[0]
        if len(self.tail) == CONTEXT + DONOR:
            key, donor = bytes(self.tail[:CONTEXT]), bytes(self.tail[CONTEXT:])
            self.bank[self.slot(key)] = (key, donor, self.position - DONOR)
        self.pending = False

    def snapshot(self):
        active = None
        if self.active is not None:
            active = {}
            for arm, model in self.active.items():
                row = dict(position=model.position, donor=model.donor.hex())
                if isinstance(model, core.EditTransducer):
                    row.update(weights=[[offset, mode, value] for (offset, mode), value
                                        in sorted(model.weights.items())], last_mode_mass=model.last_mode_mass)
                active[arm] = row
        return dict(frontend=self.frontend, position=self.position, pending=self.pending,
                    tail=self.tail.hex(), bank=[None if row is None else
                    [row[0].hex(), row[1].hex(), row[2]] for row in self.bank],
                    active=active, steps=self.steps, source_start=self.source_start,
                    triggers=self.triggers, source_sha256=SOURCE_SHA256)

    def state_digest(self):
        return hashlib.sha256(json.dumps(self.snapshot(), sort_keys=True,
                                        separators=(',', ':')).encode()).hexdigest()
