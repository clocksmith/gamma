"""Request-local associative delta updates; no learned controller or base mutation."""
import numpy as np


def derive(base, keys, values, rate=0.5, epsilon=1e-9):
    base = np.asarray(base, dtype=np.float64)
    keys = np.asarray(keys, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)
    if base.ndim != 2 or keys.ndim != 2 or values.ndim != 2:
        raise ValueError("Matrices required")
    if keys.shape != (len(values), base.shape[1]) or values.shape[1] != base.shape[0]:
        raise ValueError("Demonstration dimensions do not match base")
    if not all(np.isfinite(x).all() for x in (base, keys, values)):
        raise ValueError("Nonfinite input")
    if not np.isfinite(rate) or not 0 <= rate <= 1 or not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("Invalid fixed rate or epsilon")
    left, right = [], []
    for key, value in zip(keys, values, strict=True):
        prediction = base @ key
        if left:
            prediction += np.stack(left).T @ (np.stack(right) @ key)
        left.append(rate * (value - prediction) / (key @ key + epsilon))
        right.append(key.copy())
    return (np.array(left).reshape(-1, base.shape[0]).T,
            np.array(right).reshape(-1, base.shape[1]))


def apply(base, left, right, queries):
    return queries @ base.T + (queries @ right.T) @ left.T
