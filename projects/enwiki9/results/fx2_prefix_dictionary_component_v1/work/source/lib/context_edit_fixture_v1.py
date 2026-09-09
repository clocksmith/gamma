"""Synthetic raw-byte bridge to the existing coder; no competitive-parent claim."""
import hashlib
import json
from lib import predictor
from lib.context_edit_continuation_v1 import Continuation, core

ARMS = ('P', 'K', 'L', 'D', 'S')


class Fixture:
    frontend = predictor.RAW_MSB

    def __init__(self, arm):
        if arm not in ARMS:
            raise ValueError('unknown arm')
        self.arm = arm
        self.parent = predictor.CountingPredictor(order=8)
        self.expert = Continuation('synthetic-raw-byte-v1')
        self.mixtures = {a: core.SleepingMixture() for a in ('L', 'D', 'S')}
        self.histograms = None
        self.prefix = self.bits = 0
        self.pending = None
        self.probability_chain = hashlib.sha256()
        self.boundary_chain = hashlib.sha256()
        self.boundaries = 0

    def predict(self):
        if self.pending is not None:
            raise ValueError('observe pending truth first')
        if self.bits == 0:
            self.histograms = self.expert.predict()
        p = self.parent.predict()
        candidates = {a: None if h is None else core.conditional_p1(h, self.prefix, self.bits)
                      for a, h in self.histograms.items()}
        predictions = {a: self.mixtures[a].predict(p, q) for a, q in candidates.items()}
        q = p if self.arm in ('P', 'K') else predictions[self.arm]
        self.pending = (p, candidates)
        self.probability_chain.update(q.to_bytes(2, 'little'))
        return q

    def update(self, truth):
        if self.pending is None:
            raise ValueError('prediction required before truth')
        p, candidates = self.pending
        self.parent.update(truth)
        for arm, probability in candidates.items():
            self.mixtures[arm].observe(p, probability, truth)
        self.prefix = (self.prefix << 1) | truth
        self.bits += 1
        self.pending = None
        if self.bits == 8:
            self.expert.observe(self.prefix)
            self.prefix = self.bits = 0
            self.histograms = None
            self.boundary_chain.update(self.state_bytes())
            self.boundaries += 1

    def state_bytes(self):
        # Arm selects only the external coded probability; all model updates run
        # in every arm. This projection therefore supports the P/K identity check.
        return predictor.canonical(dict(parent=self.parent.serialize().hex(), expert=self.expert.snapshot(),
            mixtures={a:dict(parent_weight=m.parent_weight,awake_updates=m.awake_updates)
                      for a,m in self.mixtures.items()}, histograms=self.histograms,
            prefix=self.prefix,bits=self.bits,pending=self.pending))

    def witness(self):
        return dict(probability_sha256=self.probability_chain.hexdigest(),
                    byte_boundary_state_sha256=self.boundary_chain.hexdigest(),
                    byte_boundaries=self.boundaries,terminal_state_sha256=hashlib.sha256(self.state_bytes()).hexdigest(),
                    triggers=self.expert.triggers,scope='Every returned pre-truth probability and every-byte model-state projection; fixture coder exact inverse/repeat is checked separately.')
