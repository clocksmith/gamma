"""Offline study: how should a table's examples be turned into state for a frozen model?

Usage: python discover_v5.py DUMP_DIR LM_HEAD_F32 OUT_JSON [RECEIPT_JSON]      (needs numpy; no model, no GPU)
       python discover_v5.py --self-test

DUMP_DIR comes from run_v5.mjs with B1_DUMP_FEATURES; LM_HEAD_F32 from dump_head_v5.mjs. Everything here reads
only what a compiler could see (support rows and their labels) to build each method, and uses question labels
only to score. A write into the LAST layer's MLP output is simulated exactly: nothing downstream reads it but
the final norm and the output matrix, so new logits = lm_head @ (g * rmsnorm(h + write)).

Methods, all scored on the same questions:
  in-context (table present, through the cached prompt): free decode, constrained to the table's codes,
      batch-calibrated, and calibrated on the table's own lines;
  readouts with the table removed or present: ridge classifier and nearest-neighbour vote on chosen features;
  a last-layer adapter compiled from the classifier (rank = number of answer tokens), scored by full-vocabulary
      argmax at every answer position with the true answer fed in (so a "string" is right only if every position
      is), with the table removed and with it present.
"""
import collections, json, os, sys
import numpy as np


# ---------- small numerics ----------------------------------------------------------------------------------
def standardizer(X):
    mu = X.mean(0)
    sd = X.std(0)
    inv = 1.0 / (sd + 0.1 * sd.mean() + 1e-8)
    return mu, inv


def ridge_fit(blocks, Y, ratio):
    """Dual ridge over one or more feature blocks, each centred, scaled and divided by its mean kernel diagonal.
    Returns a predictor and, per block, primal weights W (features x targets) with its mu and inv."""
    n = len(Y)
    K = np.zeros((n, n))
    parts = []
    for X in blocks:
        mu, inv = standardizer(X)
        Xs = (X - mu) * inv
        G = Xs @ Xs.T
        md = np.trace(G) / n
        K += G / md
        parts.append((mu, inv, Xs, md))
    lam = ratio * np.trace(K) / n
    alpha = np.linalg.solve(K + lam * np.eye(n), Y)
    weights = [(mu, inv, (Xs.T @ alpha) / md) for mu, inv, Xs, md in parts]

    def predict(qblocks):
        s = 0
        for Q, (mu, inv, W) in zip(qblocks, weights):
            s = s + ((Q - mu) * inv) @ W
        return s
    return predict, weights


def one_vs_rest(labels, k):
    Y = np.full((len(labels), k), -1.0 / max(1, k - 1))
    Y[np.arange(len(labels)), labels] = 1.0
    return Y


def fit_bias(L, y, steps=300, lr=0.5):
    """Bias per class minimising cross-entropy of softmax(L + b) on labelled rows."""
    b = np.zeros(L.shape[1])
    for _ in range(steps):
        z = L + b
        z = z - z.max(1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(1, keepdims=True)
        grad = p.mean(0) - np.bincount(y, minlength=L.shape[1]) / len(y)
        b -= lr * grad
    return b - b.mean()


class Head:
    def __init__(self, lm, g, eps):
        self.lm, self.g, self.eps = lm, g.astype(np.float32), eps

    def normed(self, H):
        H = np.asarray(H, dtype=np.float32)
        return H / np.sqrt((H * H).mean(1, keepdims=True) + self.eps) * self.g

    def at(self, H, tokens):
        return self.normed(H) @ self.lm[tokens].T

    def argmax(self, H, chunk=96):
        out = []
        for s in range(0, len(H), chunk):
            out.append((self.normed(H[s:s + chunk]) @ self.lm.T).argmax(1))
        return np.concatenate(out) if out else np.zeros(0, dtype=int)

    def direction(self, token):
        d = self.g * self.lm[token]
        return d / np.sqrt((d * d).mean() + 1e-12)


# ---------- one table -----------------------------------------------------------------------------------------
def study_table(table, dump_dir, head, dI, dH, layers_n, grid):
    row = layers_n * dI + dH
    S = np.fromfile(os.path.join(dump_dir, table["support_file"]), dtype=np.float32).reshape(-1, row)
    Q = np.fromfile(os.path.join(dump_dir, table["query_file"]), dtype=np.float32).reshape(-1, row)
    meta = table["support_rows"]
    assert len(meta) == len(S), "support rows and index disagree"
    ctx = np.array([m["context"] for m in meta])
    lab = np.array([m["label"] for m in meta])
    off = np.array([m.get("offset", 0) for m in meta])
    nxt = np.array([m.get("next_token", -1) for m in meta])
    ex = np.array([m["example"] for m in meta])
    z = lambda X, l: X[:, l * dI:(l + 1) * dI]
    hid = lambda X: X[:, layers_n * dI:]
    first = np.array(table["class_first_tokens"])
    k = len(first)

    # Questions: per answer offset one row with the table removed, then one with it present.
    qs = table["queries"]
    qrows, at = [], 0
    for q in qs:
        n_off = len(q["answer_tokens"]) + 1
        block = Q[at:at + 2 * n_off].reshape(n_off, 2, row)
        qrows.append(block)
        at += 2 * n_off
    assert at == len(Q), "query rows and index disagree"
    qy = np.array([q["label"] for q in qs])
    Qb0 = np.stack([b[0, 0] for b in qrows])
    Qc0 = np.stack([b[0, 1] for b in qrows])

    res = {}
    anchor = (off == 0) & (lab >= 0)
    iso0, cat0 = anchor & (ctx == "iso"), anchor & (ctx == "cat")

    # --- in-context, table present --------------------------------------------------------------------------
    res["icl_free"] = head.argmax(hid(Qc0)) == first[qy]
    Lq = head.at(hid(Qc0), first)
    res["icl_constrained"] = Lq.argmax(1) == qy
    res["icl_batch_calibrated"] = (Lq - Lq.mean(0)).argmax(1) == qy
    Ls = head.at(hid(S[cat0]), first)
    res["icl_calibrated_on_table_lines"] = (Lq + fit_bias(Ls, lab[cat0])).argmax(1) == qy
    late = cat0 & (ex >= np.median(ex[cat0]))
    res["icl_calibrated_on_later_lines"] = (Lq + fit_bias(head.at(hid(S[late]), first), lab[late])).argmax(1) == qy
    res["base_free_table_removed"] = head.argmax(hid(Qb0)) == first[qy]

    # --- readouts --------------------------------------------------------------------------------------------
    feats = {
        "both_layers": lambda X: [z(X, l) for l in range(layers_n)],
        "last_layer": lambda X: [z(X, layers_n - 1)],
        "final_hidden": lambda X: [hid(X)],
    }
    trains = {"iso_and_cat": iso0 | cat0, "iso": iso0, "cat": cat0}
    for fname, f in feats.items():
        for tname, mask in trains.items():
            pred, _ = ridge_fit(f(S[mask]), one_vs_rest(lab[mask], k), 0.15)
            res[f"probe[{fname}|train {tname}] table removed"] = pred(f(Qb0)).argmax(1) == qy
            res[f"probe[{fname}|train {tname}] table present"] = pred(f(Qc0)).argmax(1) == qy
    for shots in (3, 5, 10):
        keep = (iso0 | cat0) & (np.array([np.sum((lab[iso0] == l) & (ex[iso0] < e)) for l, e in zip(lab, ex)]) < shots)
        if len(set(lab[keep])) == k:
            pred, _ = ridge_fit(feats["both_layers"](S[keep]), one_vs_rest(lab[keep], k), 0.15)
            res[f"probe[both_layers|first {shots} examples per code] table removed"] = pred(feats["both_layers"](Qb0)).argmax(1) == qy
    # nearest-neighbour vote, both layers, iso and cat rows
    mask = iso0 | cat0
    sims = 0
    for l in range(layers_n):
        mu, inv = standardizer(z(S[mask], l))
        a = (z(S[mask], l) - mu) * inv
        a /= np.linalg.norm(a, axis=1, keepdims=True) + 1e-12
        b = (z(Qb0, l) - mu) * inv
        b /= np.linalg.norm(b, axis=1, keepdims=True) + 1e-12
        sims = sims + b @ a.T / layers_n
    w = np.exp((sims - sims.max(1, keepdims=True)) / 0.08)
    votes = np.stack([w[:, lab[mask] == c].sum(1) for c in range(k)], 1)
    res["nearest_neighbour[both_layers] table removed"] = votes.argmax(1) == qy

    # --- last-layer adapter compiled from a next-token classifier --------------------------------------------
    answer = (lab >= 0) & ((ctx == "iso") | (ctx == "cat"))
    tokens = sorted(set(int(t) for t in nxt[answer]))
    tix = {t: i for i, t in enumerate(tokens)}
    zl = lambda X: z(X, layers_n - 1)
    Xa, ya = zl(S[answer]), np.array([tix[int(t)] for t in nxt[answer]])
    D = np.stack([head.direction(t) for t in tokens])                       # targets x hidden
    rms = float(np.median(np.sqrt((hid(S[answer]) ** 2).mean(1))))
    background = (ctx == "iso_background") | (ctx == "cat_background")
    variants = {}
    pred, wts = ridge_fit([Xa], one_vs_rest(ya, len(tokens)), 0.15)
    variants["answer rows only"] = pred
    if background.any():
        Xb = zl(S[background])
        Yb = np.zeros((len(Xb), len(tokens)))
        predb, wtsb = ridge_fit([np.concatenate([Xa, Xb])], np.concatenate([one_vs_rest(ya, len(tokens)), Yb]), 0.15)
        variants["with quiet background rows"] = predb
        # How loud is each variant away from an answer position? Largest absolute score on background rows.
        res["_adapter_background_peak_answer_only"] = float(np.abs(pred([Xb])).max())
        res["_adapter_background_peak_with_background"] = float(np.abs(predb([Xb])).max())
    # An adapter has no bias input. Centring is folded in through a direction a0 with a0 . x close to 1 on answer rows.
    mu, inv, W = wts[0]
    Xs = Xa * inv
    a0 = np.linalg.solve(Xs @ Xs.T + 0.15 * np.trace(Xs @ Xs.T) / len(Xs) * np.eye(len(Xs)), np.ones(len(Xs)))
    a0 = (Xs.T @ a0) * inv                                                   # a0 . x ~ 1
    A = inv[:, None] * W - np.outer(a0, (mu * inv) @ W)                      # features x targets, no bias needed
    variants["answer rows only, as a real adapter (no bias term)"] = lambda blocks: blocks[0] @ A
    res["_a0_fit_on_questions"] = [float(np.mean(zl(Qb0) @ a0)), float(np.std(zl(Qb0) @ a0))]

    for vname, score in variants.items():
        for beta in grid:
            for regime, col in (("table removed", 0), ("table present", 1)):
                ok_all = np.ones(len(qs), dtype=bool)
                ok_first = np.zeros(len(qs), dtype=bool)
                for qi, (q, block) in enumerate(zip(qs, qrows)):
                    gold = list(q["answer_tokens"]) + [None]
                    X = block[:, col]
                    Hn = hid(X) + beta * rms * (score([zl(X)]) @ D)
                    got = head.argmax(Hn)
                    for o, g in enumerate(gold):
                        want = g if g is not None else table["_newline"]
                        right = int(got[o]) == int(want)
                        if o == 0:
                            ok_first[qi] = right
                        ok_all[qi] &= right
                res[f"adapter[{vname}|gain {beta}] {regime}: first token"] = ok_first
                res[f"adapter[{vname}|gain {beta}] {regime}: whole answer"] = ok_all
    res["_adapter_rank"] = len(tokens)
    res["_adapter_bytes_f32"] = (dI + dH) * len(tokens) * 4
    res["_task_ids"] = [q["task_id"] for q in qs]
    return res


def run(dump_dir, lm_path, out_path, receipt_path=None, grid=(0.5, 1.0, 2.0, 4.0)):
    idx = json.load(open(os.path.join(dump_dir, "index.json")))
    shape = json.load(open(lm_path + ".json"))["shape"]
    lm = np.fromfile(lm_path, dtype=np.float32).reshape(shape)
    head = Head(lm, np.array(idx["final_norm_weight"]), idx.get("rms_norm_eps") or 1e-6)
    dI, dH, layers_n = idx["intermediate_size"], idx["hidden_size"], len(idx["layers"])
    totals = collections.defaultdict(list)
    extras = collections.defaultdict(list)
    per_table = {}
    task_ids = []
    for table in idx["tables"]:
        table["_newline"] = idx["newline_token"]
        r = study_table(table, dump_dir, head, dI, dH, layers_n, grid)
        task_ids += r.pop("_task_ids")
        per_table[table["specialty_id"]] = {}
        for name, v in r.items():
            if name.startswith("_"):
                extras[name].append(v)
            else:
                totals[name].append(np.asarray(v))
                per_table[table["specialty_id"]][name] = float(np.mean(v))
    n = len(task_ids)
    summary = {name: {"correct": int(np.concatenate(v).sum()), "of": n, "share": round(float(np.concatenate(v).mean()), 4)} for name, v in totals.items()}
    out = {"model": idx["model"], "seed": idx["seed"], "tables": len(idx["tables"]), "questions": n, "methods": summary,
           "adapter": {"rank_per_table": sorted(set(extras["_adapter_rank"])), "bytes_f32": sorted(set(extras["_adapter_bytes_f32"])),
                       "background_peak_answer_only": float(np.mean(extras["_adapter_background_peak_answer_only"])) if extras["_adapter_background_peak_answer_only"] else None,
                       "background_peak_with_background": float(np.mean(extras["_adapter_background_peak_with_background"])) if extras["_adapter_background_peak_with_background"] else None,
                       "a0_on_questions_mean_and_sd": np.mean(np.array(extras["_a0_fit_on_questions"]), 0).round(4).tolist()},
           "per_table": per_table}
    if receipt_path:
        rec = json.load(open(receipt_path))
        by = collections.defaultdict(dict)
        for row in rec["rows"]:
            by[row["arm"]][row["task_id"]] = row
        out["receipt_arms"] = {arm: {"correct": sum(bool(by[arm][t]["correct"]) for t in task_ids if t in by[arm]), "of": sum(t in by[arm] for t in task_ids)} for arm in sorted(by)}
        # Does the simulation agree with what the runtime actually generated first?
        checks = {}
        for arm, name in (("kv_ctx", "icl_free"), ("base_bare", "base_free_table_removed")):
            if arm in by:
                sim = np.concatenate(totals[name])
                gpu = np.array([bool(by[arm][t]["correct"]) for t in task_ids])
                checks[f"{name} against {arm}"] = {"same_verdict": int((sim == gpu).sum()), "of": n}
        out["simulation_check"] = checks
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    width = max(len(k) for k in summary)
    for name, v in sorted(summary.items(), key=lambda kv: -kv[1]["share"]):
        print(f"{name:<{width}}  {v['correct']:4d}/{v['of']}  {100 * v['share']:5.1f}%")
    for key in ("adapter", "receipt_arms", "simulation_check"):
        if key in out:
            print(key, json.dumps(out[key]))
    return out


def self_test():
    """Synthetic dump with a planted, linearly readable code: every method should run and the readouts should be right."""
    import tempfile
    rng = np.random.default_rng(1)
    dI, dH, V, k, shots, nq = 40, 24, 300, 4, 6, 8
    lm = rng.normal(0, 1, (V, dH)).astype(np.float32)
    codes, newline = [11, 22, 33, 44], 7
    cls = rng.normal(0, 1, (k, dI))
    shared = rng.normal(0, 4, dI)

    def row(label, noise=0.6):
        zz = [shared + cls[label] + rng.normal(0, noise, dI) for _ in range(2)]
        h = rng.normal(0, 1, dH) + 0.5 * lm[codes[label]]
        return np.concatenate(zz + [h]).astype(np.float32)

    def stop_row():
        return np.concatenate([shared + rng.normal(0, 0.6, dI) + 3, shared + rng.normal(0, 0.6, dI) + 3, rng.normal(0, 1, dH)]).astype(np.float32)

    with tempfile.TemporaryDirectory() as d:
        rows, meta = [], []
        for context in ("iso", "cat"):
            for e in range(shots * k):
                rows.append(row(e % k)); meta.append({"context": context, "example": e, "label": e % k, "offset": 0, "next_token": codes[e % k]})
                rows.append(stop_row()); meta.append({"context": context, "example": e, "label": e % k, "offset": 1, "next_token": newline})
        for e in range(8):
            rows.append(np.concatenate([shared - 3 + rng.normal(0, 0.6, dI)] * 2 + [rng.normal(0, 1, dH)]).astype(np.float32))
            meta.append({"context": "iso_background", "example": e, "label": -1, "offset": -1, "next_token": -1})
        np.stack(rows).tofile(os.path.join(d, "t.support.f32"))
        qrows, queries = [], []
        for qi in range(nq):
            for _context in (0, 1):
                pass
            y = qi % k
            qrows += [row(y), row(y), stop_row(), stop_row()]
            queries.append({"task_id": qi, "expected": str(y), "label": y, "group": "g", "answer_tokens": [codes[y]], "rows": 4})
        np.stack(qrows).tofile(os.path.join(d, "t.query.f32"))
        json.dump({"model": "synthetic", "seed": 0, "layers": [0, 1], "hidden_size": dH, "intermediate_size": dI, "newline_token": newline,
                   "rms_norm_eps": 1e-6, "final_norm_weight": [1.0] * dH,
                   "tables": [{"specialty_id": "t", "class_first_tokens": codes, "support_file": "t.support.f32", "support_rows": meta,
                               "query_file": "t.query.f32", "queries": queries}]}, open(os.path.join(d, "index.json"), "w"))
        lm.tofile(os.path.join(d, "lm.f32"))
        json.dump({"shape": [V, dH]}, open(os.path.join(d, "lm.f32.json"), "w"))
        out = run(d, os.path.join(d, "lm.f32"), os.path.join(d, "out.json"), grid=(4.0, 16.0))
    m = out["methods"]
    assert m["probe[both_layers|train iso_and_cat] table removed"]["share"] == 1.0, m
    assert m["adapter[answer rows only|gain 16.0] table removed: whole answer"]["share"] >= 0.75, m
    assert m["adapter[answer rows only, as a real adapter (no bias term)|gain 16.0] table removed: first token"]["share"] >= 0.75, m
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    elif len(sys.argv) >= 4:
        run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        print(__doc__)
        sys.exit(2)
