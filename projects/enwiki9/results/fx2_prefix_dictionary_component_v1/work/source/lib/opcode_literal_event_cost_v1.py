"""Bounded encoder-only literal-event costs; the authoritative models stay untouched."""
import math

MAX_SPAN = 258


def literal_event_costs(models, keys):
    """Price consecutive zero events using the compact codec's exact count laws.

    Models maps decoder-context tuples to CM instances. Keys must describe the
    already chosen byte span; encoder lookahead does not become decoder input.
    Returned floating costs guide search, not a finite-archive certificate.
    """
    if len(keys) > MAX_SPAN:
        raise ValueError('literal span exceeds frozen bound')
    local, probabilities, cumulative = {}, [], [0.0]
    for key in keys:
        if key not in local:
            model = models.get(key)
            counts = list(model.c) if model is not None else [1, 1, 1]
            if len(counts) != 3 or any(type(c) is not int or c <= 0 for c in counts):
                raise ValueError('invalid literal-event counts')
            if model is not None and model.t != sum(counts):
                raise ValueError('literal-event total differs')
            local[key] = counts
        counts = local[key]
        total = sum(counts)
        probabilities.append((counts[0], total))
        cumulative.append(cumulative[-1] + math.log2(total / counts[0]))
        counts[0] += 1
        if total + 1 > 4096:
            counts[:] = [(c + 1) // 2 for c in counts]
    return cumulative, probabilities
