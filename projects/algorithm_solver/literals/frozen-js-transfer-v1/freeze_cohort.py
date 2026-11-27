"""Freeze and materialize whole, owner-disjoint repositories for the JavaScript transfer card."""
import argparse
import ast
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
SEED = "bits/frozen-js-transfer/v1"
SEARCH = ("language:JavaScript license:mit size:1..60 stars:100..10000 "
          "fork:false archived:false mirror:false created:<2023-01-01")
FILE_MODES = {"100644", "100755"}
TARGET = 20


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode()


def freeze(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"freeze conflict at {path}")
        return
    with path.open("xb") as out:
        out.write(data)


def load(name):
    return json.loads((HERE / name).read_bytes())


def api(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint]))


def search(cache):
    out = []
    for page, filename in [(page, f"discovery-raw-{page}.json") for page in (3, 4, 5)]:
        raw_path = cache / filename
        if not raw_path.exists():
            params = dict(q=SEARCH, per_page=100, page=page, sort="stars", order="desc")
            freeze(raw_path, encoded(api("search/repositories?" + urlencode(params))))
        data = json.loads(raw_path.read_bytes())
        if data["incomplete_results"] or len(data["items"]) != 100:
            raise ValueError("incomplete candidate frame")
        for item in data["items"]:
            out.append({
                "repository": item["full_name"], "repository_id": item["id"],
                "owner_id": item["owner"]["id"], "page": page, "branch": item["default_branch"],
                "description": item["description"], "topics": item["topics"],
                "stars": item["stargazers_count"], "repository_size_kib": item["size"],
                "spdx": item["license"]["spdx_id"], "language": item["language"],
            })
    freeze(HERE / "candidate_frame.json", encoded({"query": SEARCH, "repositories": out}))


def registry():
    lit = HERE.parent
    source = "a1b-horizon-sizing-v1/calibration_corpora.py"
    tree = ast.parse((lit / source).read_bytes())
    constants = {s.target.id: ast.literal_eval(s.value)
                 for s in tree.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
                 and s.target.id == "CAPACITY_ORG_ALIASES"}
    reserved = next(s for s in tree.body if isinstance(s, ast.Assign)
                    and isinstance(s.targets[0], ast.Name)
                    and s.targets[0].id == "RESERVED_SEALED_DOMAIN_TOKENS")
    domains = ast.literal_eval(reserved.value.args[0])
    cal_path = "a1b-horizon-sizing-v1/out/calibration_manifest.json"
    cal = json.loads((lit / cal_path).read_bytes())
    audit = cal["disjointness_audit"]
    forbidden = {"ibm", "ineil77", "codenet", "express", "thealgorithms",
                 "clocksmith", "github", "leetcode", "hackerrank"}
    forbidden.update(audit["fit_and_predictor_fit_orgs_checked"])
    aliases = constants["CAPACITY_ORG_ALIASES"]
    for name in audit["capacity_sources_checked"]:
        forbidden.update(aliases[name])
        forbidden.add(name)
    raw = set()
    squeezed = set()
    sources = {source, cal_path}
    for item in cal["calibration_orgs"]:
        forbidden.update([item["org_id"], *item["upstream_repo"].split("/")])
        raw.update(item["file_hashes"])
    for parent in ["objective-holdout-v1/frozen/sets", "objective-holdout-v1/sets",
                   "closure-holdout-v1/sets"]:
        for path in sorted((lit / parent).glob("*.json")):
            sources.add(str(path.relative_to(lit)))
            for item in json.loads(path.read_bytes())["files"]:
                raw.add(item["sha256"])
    split = "a2-recursive-frames-v1/corpus_split.json"
    sources.add(split)
    obj = json.loads((lit / split).read_bytes())
    for item in obj["train"] + obj["dev"]:
        raw.add(item["raw_sha256"])
        squeezed.add(item["squeezed_sha256"])
    historical = (HERE / "history-squeezed-sha256.txt").read_bytes()
    if sha(historical) != "768035fbbc61b94053681e5fb624830db07e0f165852ac297efaa942b60ee508":
        raise ValueError("historical fingerprint receipt mismatch")
    squeezed.update(historical.decode("ascii").splitlines())
    for name, expected in cal["capacity_audit_files_sha256"].items():
        if sha((lit / name).read_bytes()) != expected:
            raise ValueError(f"capacity manifest changed: {name}")
        sources.add(name)
    provenance = {name: sha((lit / name).read_bytes()) for name in sorted(sources)}
    summary = {"input_sha256": provenance, "capacity_corpora": audit["capacity_ladder_corpus_count_checked"],
               "excluded_identity_tokens": sorted({t.lower() for t in forbidden}),
               "reserved_domain_tokens": sorted(domains), "historical_exact_hashes": len(raw),
               "historical_squeezed_hashes": len(squeezed), "history_index_sha256": sha(historical)}
    return summary, raw, squeezed


def rank(repo):
    return sha((SEED + "\0" + repo["repository"].casefold()).encode())


def pin(repo):
    name = repo["repository"]
    owner, name_only = name.split("/")
    query = ("query($owner:String!,$name:String!) {repository(owner:$owner,name:$name)"
             "{defaultBranchRef{name target{... on Commit{oid tree{oid}}}}}}")
    result = json.loads(subprocess.check_output([
        "gh", "api", "graphql", "-f", "query=" + query, "-f", "owner=" + owner, "-f", "name=" + name_only]))
    branch = result["data"]["repository"]["defaultBranchRef"]
    if branch["name"] != repo["branch"]:
        raise ValueError(f"default branch changed for {name}")
    tip = branch["target"]["oid"]
    tree = branch["target"]["tree"]["oid"]
    listing = api(f"repos/{name}/git/trees/{tree}?recursive=1")
    if listing["truncated"] or listing["sha"] != tree:
        raise ValueError(f"incomplete tree for {name}")
    files = sorted([dict(path=f["path"], blob=f["sha"], bytes=f["size"], mode=f["mode"])
                    for f in listing["tree"] if f["type"] == "blob" and f["mode"] in FILE_MODES
                    and f["path"].endswith(".js")], key=lambda f: f["path"])
    size = sum(f["bytes"] for f in files)
    good = (1 <= len(files) <= 25 and 256 <= size <= 16000
            and all(0 < f["bytes"] <= 8192 for f in files))
    result = {"repository": name, "owner_id": repo["owner_id"], "rank": rank(repo), "commit": tip,
              "tree": tree, "js_files": len(files), "js_bytes": size, "eligible": good}
    if good:
        result["files"] = files
    return result


def select_pins():
    summary, _, _ = registry()
    frame = load("candidate_frame.json")
    eligible = []
    skipped = []
    discarded = load("discarded_frame.json")
    discarded_ids = set(discarded["excluded_repository_ids"])
    discarded_owners = set(discarded["excluded_owner_ids"])
    seen = set()
    for item in sorted(frame["repositories"], key=rank):
        name = item["repository"]
        if item["repository_id"] in discarded_ids or item["owner_id"] in discarded_owners:
            skipped.append([name, "discarded preliminary repository or owner"])
            continue
        if item["repository_id"] in seen:
            skipped.append([name, "duplicate GitHub search row"])
            continue
        seen.add(item["repository_id"])
        components = {part.lower() for part in name.split("/")}
        tokens = components | set(re.findall(r"[a-z0-9]+", name.lower()))
        text = " ".join([name, item["description"] or "", *item["topics"]]).lower()
        domain_tokens = set(re.findall(r"[a-z0-9]+", text))
        hits = sorted((tokens & set(summary["excluded_identity_tokens"]))
                      | (domain_tokens & set(summary["reserved_domain_tokens"])))
        if hits:
            skipped.append([name, "reserved/spent metadata match", hits])
        else:
            eligible.append(item)
    # Bound network work, with all candidates and their order fixed before byte access.
    ranked = eligible[:100]
    with ThreadPoolExecutor(max_workers=5) as pool:
        pins = list(pool.map(pin, ranked))
    if sum(p["eligible"] for p in pins) < TARGET:
        raise ValueError("insufficient metadata-eligible repositories")
    freeze(HERE / "selection_pins.json", encoded({
        "candidate_frame_sha256": sha((HERE / "candidate_frame.json").read_bytes()),
        "registry": summary, "seed": SEED, "excluded_by_metadata": skipped,
        "post_metadata_pool": len(eligible), "pinned": pins,
    }))


def file_path(repo, path):
    rel = PurePosixPath(repo, path)
    if rel.is_absolute() or ".." in rel.parts or any(x in path for x in ("\\", "\0")):
        raise ValueError("unsafe upstream path")
    return rel


def materialize(cache):
    import base64
    pins = load("selection_pins.json")
    summary, raw, squeezed = registry()
    if pins["registry"] != summary:
        raise ValueError("exclusion registry changed")
    owners = set()
    selected = []
    rejected = []
    files = []
    blobs = cache / "blobs"
    blobs.mkdir(exist_ok=True)
    all_raw = set(raw)
    all_squeezed = set(squeezed)
    for p in pins["pinned"]:
        if not p["eligible"]:
            continue
        repo = p["repository"]
        if p["owner_id"] in owners:
            rejected.append({"repository": repo, "reason": "same selected owner"})
            continue
        repo_raw = set()
        repo_squeezed = set()
        matched = []
        staged = []
        for f in p["files"]:
            ref = f["blob"]
            dest = blobs / ref
            if not dest.exists():
                d = api(f"repos/{repo}/git/blobs/{ref}")
                if d["sha"] != ref or d["encoding"] != "base64":
                    raise ValueError("unexpected Git blob")
                freeze(dest, base64.b64decode(d["content"]))
            buf = dest.read_bytes()
            if len(buf) != f["bytes"] or hashlib.sha1(
                    b"blob " + str(len(buf)).encode() + b"\0" + buf).hexdigest() != ref:
                raise ValueError(f"corrupt Git blob {ref}")
            h = sha(buf)
            sq = sha(b"".join(buf.split()))
            if h in all_raw or h in repo_raw or sq in all_squeezed or sq in repo_squeezed:
                matched.append({"path": f["path"], "sha256": h, "squeezed_sha256": sq,
                                "exact_duplicate": h in all_raw or h in repo_raw,
                                "squeezed_duplicate": sq in all_squeezed or sq in repo_squeezed})
            repo_raw.add(h)
            repo_squeezed.add(sq)
            rel = str(file_path(repo, f["path"]))
            staged.append((dict(lineage=repo, path=rel, sha256=h, squeezed_sha256=sq,
                                bytes=len(buf), blob=ref), buf))
        if matched:
            rejected.append({"repository": repo, "reason": "whole repository duplicate rejection",
                             "duplicates": matched})
            continue
        for row, buf in staged:
            dest = cache / "corpus" / row["path"]
            dest.parent.mkdir(exist_ok=True, parents=True)
            freeze(dest, buf)
            files.append(row)
        all_raw.update(repo_raw)
        all_squeezed.update(repo_squeezed)
        selected.append({k: v for k, v in p.items() if k not in {"eligible", "files"}})
        owners.add(p["owner_id"])
        if len(selected) == TARGET:
            break
    if len(selected) != TARGET:
        raise ValueError("fewer than 20 whole eligible repositories, retain failure")
    manifest = {"schema":"bits.frozen-js-transfer.sources.v1", "files":files, "lineages":selected}
    freeze(HERE / "source_manifest.json", encoded(manifest))
    freeze(HERE / "cohort_audit.json", encoded({
        "selection_pins_sha256": sha((HERE / "selection_pins.json").read_bytes()),
        "source_manifest_sha256": sha(encoded(manifest)), "selected_repositories": len(selected),
        "selected_owners": len(owners), "js_files": len(files), "js_bytes": sum(x["bytes"] for x in files),
        "rejections_during_traversal": rejected, "distinct_exact": len({x["sha256"] for x in files}),
        "distinct_squeezed": len({x["squeezed_sha256"] for x in files}),
        "historical_raw_overlap": len({x["sha256"] for x in files} & raw),
        "historical_squeezed_overlap": len({x["squeezed_sha256"] for x in files} & squeezed),
    }))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=["frame", "pin", "materialize"])
    p.add_argument("--cache", type=Path, required=True)
    args = p.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    if args.stage == "frame":
        search(args.cache)
    elif args.stage == "pin":
        select_pins()
    else:
        materialize(args.cache)
