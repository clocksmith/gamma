"""Synthetic alias-context feasibility codec; no natural-text compression claim."""
import hashlib
import json
import re
from fixture_coder import Predictor, CountingPredictor, RAW_MSB, canonical, encode, decode


class Model(Predictor):
    def __init__(self, arm='D'):
        super().__init__(RAW_MSB)
        if arm not in ('P', 'K', 'D', 'S'):
            raise ValueError('unknown arm')
        self.arm = arm
        self.base = CountingPredictor(8)
        self.rows = {}
        self.table_root = 0
        self.queue = hashlib.sha256()
        self.aliases = {}
        self.line = b''
        self.overflow = False
        self.entity = b''
        self.last = 0
        self.node = 1
        self.probabilities = hashlib.sha256()
        self.boundaries = hashlib.sha256()
        self.boundary_count = 0

    def key(self):
        entity = self.entity
        if self.arm in ('D', 'S') and entity in self.aliases:
            if self.arm == 'D':
                entity = self.aliases[entity]
            else:
                keys = list(self.aliases)
                entity = self.aliases[keys[(keys.index(entity) + 1) % len(keys)]]
        return (entity, self.last, self.node)

    @staticmethod
    def entry(key, counts):
        return int.from_bytes(hashlib.sha256(canonical(
            [key[0].hex(), key[1], key[2], counts])).digest(), 'big')

    def _predict(self):
        base = self.base.predict()
        row = self.rows.get(self.key()) if self.entity else None
        p = base if row is None else (base + 3 * (65536 * row[1] // sum(row))) // 4
        p = max(1, min(65535, p))
        self.probabilities.update(p.to_bytes(2, 'big'))
        return p

    def _update(self, bit):
        self.base.update(bit)
        if self.entity:
            key = self.key()
            if key not in self.rows:
                if len(self.rows) == 4096:
                    old = next(iter(self.rows))
                    self.table_root ^= self.entry(old, self.rows.pop(old))
                    self.queue.update(canonical(['evict', old[0].hex(), *old[1:]]))
                self.rows[key] = [1, 1]
                self.table_root ^= self.entry(key, self.rows[key])
                self.queue.update(canonical(['insert', key[0].hex(), *key[1:]]))
            row = self.rows[key]
            self.table_root ^= self.entry(key, row)
            row[bit] += 1
            if sum(row) >= 32768:
                row[:] = [max(1, (n + 1) // 2) for n in row]
            self.table_root ^= self.entry(key, row)
        self.node = self.node * 2 + bit
        if self.node >= 256:
            byte = self.node - 256
            self.node = 1
            if byte == 10:
                if self.arm != 'P' and not self.overflow:
                    m = re.fullmatch(rb'([A-Z][A-Za-z]*(?: [A-Z][A-Za-z]*){1,7}) \(([A-Z]{2,8})\)', self.line)
                    if m and bytes(word[0] for word in m[1].split()) == m[2]:
                        if m[2] not in self.aliases and len(self.aliases) == 16:
                            del self.aliases[next(iter(self.aliases))]
                        self.aliases[m[2]] = m[1]
                self.line = b''
                self.overflow = False
                self.entity = b''
            else:
                if byte == 58 and not self.entity and not self.overflow:
                    self.entity = self.line
                if len(self.line) < 128:
                    self.line += bytes([byte])
                else:
                    self.overflow = True
            self.last = byte
            self.boundary_count += 1
            # Compares all prediction-relevant state at every byte. Table root
            # is an XOR of entry hashes; queue chain witnesses FIFO history.
            state = [self.base.state_digest(), str(self.table_root), self.queue.hexdigest(),
                     self.line.hex(), self.overflow, self.entity.hex(), self.last, self.node]
            if self.arm in ('D', 'S'):
                state.append([(k.hex(), v.hex()) for k, v in self.aliases.items()])
            self.boundaries.update(canonical(state))

    def _export_state(self):
        return dict(base=self.base._export_state(), rows=[
            [k[0].hex(), *k[1:], v] for k, v in self.rows.items()],
            aliases=[(k.hex(), v.hex()) for k, v in self.aliases.items()],
            line=self.line.hex(), overflow=self.overflow, entity=self.entity.hex(),
            last=self.last, node=self.node)

    @classmethod
    def restore(cls, payload, frontend=RAW_MSB):
        raise NotImplementedError('Fixture restarts cold; state resumption is not exposed')

    def audit(self):
        return dict(probabilities=self.probabilities.hexdigest(), boundaries=self.boundaries.hexdigest(),
                    boundary_count=self.boundary_count, final_state=self._export_state())


def compress(data):
    return encode(data, Model())


def decompress(archive):
    return decode(archive, Model())


if __name__ == '__main__':
    import sys
    from pathlib import Path
    mode, arm, source, output, audit = sys.argv[1:]
    model = Model(arm)
    raw = Path(source).read_bytes()
    result = encode(raw, model) if mode == 'encode' else decode(raw, model)
    Path(output).write_bytes(result)
    Path(audit).write_text(json.dumps(model.audit(), sort_keys=True) + '\n')
