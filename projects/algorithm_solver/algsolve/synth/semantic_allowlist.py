"""Source-free development allowlist compiler and fail-closed dataset/teacher adapters.

Enforces explicit authorized-development allowlisting and transitive exclusion
across aliases, semantic families, slug sibling stems and structural groups
before any problem statement, starter code, or test payload is parsed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

from .. import importers, test_corrections, values
from ..rebuild_download import FILES, verify as verify_pinned_download
from ..records import INDEPENDENT, LANE_ROOT, Problem
from ..splits import sibling_base
from . import semantic_target_pipeline as pipeline


SCHEMA = "algsolve.semantic-development-allowlist.v1"
COMMITTED_AUTHORITY_PATHS = (
    "catalogue/PROBLEM_INDEX.jsonl",
    "literals/cost-decomposition-v1/contract.json",
    "contracts/sample_manifest.json",
    "contracts/typed_confirmation_v1.json",
    "contracts/js_corpus_reservations_v1.json",
    "findings/known-lookup-release-v2/approved-library.json",
    "literals/scale-v2/protected-boundary.json",
)
FORBIDDEN_TEACHER_KEYS = frozenset({
    "reference_solutions", "completion", "response", "solution",
    "independent_tests", "hidden_tests", "test", "tests",
    "verdict", "verdicts", "judge_feedback", "error",
})


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _nonempty_str(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label}")
    return value


def _row_identity_tokens(row: dict) -> list[str]:
    tokens = {"id:" + row["key"]}
    if row.get("source") == "leetcode" and str(row.get("id", "")).isdigit():
        nid = int(row["id"])
        tokens.update((f"id:lcd:{nid}", f"id:leetcode:{nid}", f"id:doocs:{nid:04d}"))
    slug = row.get("slug")
    if isinstance(slug, str) and slug.strip():
        tokens.add("id:lc:" + slug)
        tokens.add("fam:" + sibling_base(slug))
    group_id = row.get("group_id")
    if group_id is not None and str(group_id).strip():
        tokens.add("grp:" + str(group_id).strip())
    for rel in row.get("related_leetcode") or ():
        rel_str = str(rel).strip()
        if rel_str:
            tokens.add("id:leetcode:" + rel_str)
            if rel_str.isdigit():
                nid = int(rel_str)
                tokens.add(f"id:lcd:{nid}")
                tokens.add(f"id:doocs:{nid:04d}")
    for rel in row.get("related_hack2hire") or ():
        rel_str = str(rel).strip()
        if rel_str:
            tokens.add("id:hack2hire:" + rel_str)
    return sorted(tokens)


def compile_committed_allowlist_and_boundary(lane_root: Path = LANE_ROOT) -> dict:
    """Compile the explicit development allowlist and reservation union from committed metadata.

    Reads only committed source-free metadata files (zero payload reads).
    Excludes all 4,744 non-allowlisted PROBLEM_INDEX rows, all reservations in
    sample_manifest, typed_confirmation_v1 (including development_audit),
    js_corpus_reservations_v1 (waves W001 and W002), approved-library
    protected_composition_alias entries, and every connected alias, family,
    sibling-stem or structural-group component touching any excluded entry.
    """
    lane_root = Path(lane_root).resolve()
    sources_sha256 = {}
    for rel_path in COMMITTED_AUTHORITY_PATHS:
        full_path = lane_root / rel_path
        if not full_path.is_file():
            raise FileNotFoundError(f"Missing committed authority file: {rel_path}")
        sources_sha256[rel_path] = _sha256_file(full_path)

    protected_boundary = json.loads((lane_root / "literals/scale-v2/protected-boundary.json").read_text(encoding="utf-8"))
    if protected_boundary.get("reservation_contract_sha256") != sources_sha256["contracts/typed_confirmation_v1.json"]:
        raise ValueError("protected-boundary.json reservation_contract_sha256 disagrees with typed_confirmation_v1.json")
    if protected_boundary.get("reserved_problem_overlap") != []:
        raise ValueError("protected-boundary.json reports reserved overlap")

    problem_index = [
        json.loads(line)
        for line in (lane_root / "catalogue/PROBLEM_INDEX.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cost_contract = json.loads((lane_root / "literals/cost-decomposition-v1/contract.json").read_text(encoding="utf-8"))
    sample_manifest = json.loads((lane_root / "contracts/sample_manifest.json").read_text(encoding="utf-8"))
    typed_confirmation = json.loads((lane_root / "contracts/typed_confirmation_v1.json").read_text(encoding="utf-8"))
    js_reservations = json.loads((lane_root / "contracts/js_corpus_reservations_v1.json").read_text(encoding="utf-8"))
    approved_library = json.loads((lane_root / "findings/known-lookup-release-v2/approved-library.json").read_text(encoding="utf-8"))

    dev_fit_ids = {str(x) for x in cost_contract["partition"]["dev_fit"]}
    dev_val_ids = {str(x) for x in cost_contract["partition"]["dev_val"]}
    if dev_fit_ids & dev_val_ids:
        raise ValueError("cost-decomposition-v1 dev_fit and dev_val partitions overlap")

    authorized_400 = [row for row in problem_index if row.get("boundary_status") == "previously_authorized_400"]
    if {str(row["id"]) for row in authorized_400} != (dev_fit_ids | dev_val_ids):
        raise ValueError("PROBLEM_INDEX previously_authorized_400 disagrees with cost-decomposition-v1 300+100 partition")
    if any(row.get("source") != "leetcode" or not str(row.get("id", "")).isdigit() for row in authorized_400):
        raise ValueError("Unexpected non-LeetCode entry in previously_authorized_400")

    parent: dict[str, str] = {}

    def find(token: str) -> str:
        parent.setdefault(token, token)
        while parent[token] != token:
            parent[token] = parent[parent[token]]
            token = parent[token]
        return token

    def union_all(tokens: list[str]) -> None:
        if len(tokens) < 2:
            if tokens:
                find(tokens[0])
            return
        first = find(tokens[0])
        for other in tokens[1:]:
            right = find(other)
            if first != right:
                low, high = (first, right) if first < right else (right, first)
                parent[high] = low
                first = low

    tainted_tokens: set[str] = set()
    status_counts = Counter()

    for row in problem_index:
        status = str(row.get("boundary_status") or "unknown")
        status_counts[status] += 1
        tokens = _row_identity_tokens(row)
        union_all(tokens)
        if status != "previously_authorized_400":
            tainted_tokens.update(tokens)

    for query in sample_manifest["recognition"] + sample_manifest["recognition_dev"]:
        target = query.get("target")
        if target:
            q_tokens = ["id:" + target]
            if target.startswith("lc:"):
                q_tokens.append("fam:" + sibling_base(target[3:]))
            union_all(q_tokens)
            tainted_tokens.update(q_tokens)
    for uids in sample_manifest["solving"].values():
        for uid in uids:
            find("id:" + uid)
            tainted_tokens.add("id:" + uid)
    for dropped_key in sample_manifest["near_duplicates"]["dropped_index_entries"]:
        d_tokens = ["id:" + dropped_key]
        if dropped_key.startswith("lc:"):
            d_tokens.append("fam:" + sibling_base(dropped_key[3:]))
        union_all(d_tokens)
        tainted_tokens.update(d_tokens)
    for pair in sample_manifest["near_duplicates"]["sibling_pairs_kept"]:
        p_tokens = ["id:" + pair["index_key"], "id:" + pair["pool_uid"]]
        if pair["index_key"].startswith("lc:"):
            p_tokens.append("fam:" + sibling_base(pair["index_key"][3:]))
        union_all(p_tokens)
        tainted_tokens.update(p_tokens)

    for entry in typed_confirmation["reservation"]["pool"]:
        c_tokens = [
            "id:" + entry["key"],
            "fam:" + entry["family"],
            "fam:" + sibling_base(entry["key"].removeprefix("lc:")),
            *("id:" + member for member in entry["members"]),
        ]
        if entry.get("judge_uid"):
            c_tokens.append("id:" + entry["judge_uid"])
        union_all(sorted(set(c_tokens)))
        tainted_tokens.update(c_tokens)
    for item in typed_confirmation["development"]["identities"]:
        if item.get("split") == "development_audit":
            a_tokens = [
                "id:" + item["uid"],
                "fam:" + item["family"],
                "fam:" + sibling_base(item["family"]),
            ]
            union_all(sorted(set(a_tokens)))
            tainted_tokens.update(a_tokens)

    for wave in js_reservations["waves"]:
        for row in wave["rows"]:
            nid = int(row["id"])
            w_tokens = [
                f"id:lcd:{nid}",
                f"id:leetcode:{nid}",
                f"id:doocs:{nid:04d}",
                "id:" + row["key"],
                "fam:" + row["family"],
                "fam:" + sibling_base(row["key"].removeprefix("lc:")),
            ]
            union_all(sorted(set(w_tokens)))
            tainted_tokens.update(w_tokens)

    for key, reason in approved_library["excluded"].items():
        if reason == "protected_composition_alias":
            l_tokens = ["id:" + key]
            if key.startswith("lc:"):
                l_tokens.append("fam:" + sibling_base(key[3:]))
            union_all(l_tokens)
            tainted_tokens.update(l_tokens)

    tainted_roots = {find(token) for token in tainted_tokens}

    surviving_rows = []
    contaminated_rows = []
    for row in sorted(authorized_400, key=lambda r: int(r["id"])):
        tokens = _row_identity_tokens(row)
        if any(find(token) in tainted_roots for token in tokens):
            contaminated_rows.append(row)
            tainted_tokens.update(tokens)
        else:
            surviving_rows.append(row)

    # Expand tainted_tokens to include every member of any tainted connected component.
    all_tainted_members = {token for token in parent if find(token) in tainted_roots} | tainted_tokens

    boundary_uids = sorted(
        token[3:] for token in all_tainted_members
        if token.startswith("id:") and not token[3:].startswith("lc:")
    )
    boundary_keys = sorted(
        token[3:] for token in all_tainted_members
        if token.startswith("id:lc:")
    )
    boundary_families = sorted(
        token[4:] for token in all_tainted_members
        if token.startswith("fam:")
    )
    boundary_groups = sorted(
        token[4:] for token in all_tainted_members
        if token.startswith("grp:")
    )

    allowlist_uids = []
    allowlist_keys = []
    functional_dev_fit = []
    functional_dev_val = []
    excluded_design_or_paid = 0

    for row in surviving_rows:
        nid = int(row["id"])
        uid = f"lcd:{nid}"
        allowlist_uids.extend((uid, f"leetcode:{nid}", f"doocs:{nid:04d}"))
        allowlist_keys.append("lc:" + row["slug"])
        if row.get("design") or row.get("paid_only"):
            excluded_design_or_paid += 1
        elif str(row["id"]) in dev_fit_ids:
            functional_dev_fit.append(uid)
        else:
            functional_dev_val.append(uid)

    allowlist = pipeline._validate_allowlist({
        "uids": sorted(set(allowlist_uids)),
        "keys": sorted(set(allowlist_keys)),
        "sources_sha256": copy.deepcopy(sources_sha256),
    })
    boundary = {
        "uids": boundary_uids,
        "keys": boundary_keys,
        "families": boundary_families,
        "structural_groups": boundary_groups,
        "sources_sha256": copy.deepcopy(sources_sha256),
    }

    audit = {
        "schema": SCHEMA,
        "problem_index_total": len(problem_index),
        "problem_index_by_boundary_status": dict(sorted(status_counts.items())),
        "previously_authorized_400": len(authorized_400),
        "non_allowlisted_problem_index_rows": len(problem_index) - len(authorized_400),
        "contaminated_authorized_rows": len(contaminated_rows),
        "self_contained_allowlisted_rows": len(surviving_rows),
        "excluded_design_or_paid_rows": excluded_design_or_paid,
        "functional_non_paid_candidates": len(functional_dev_fit) + len(functional_dev_val),
        "functional_dev_fit_candidates": len(functional_dev_fit),
        "functional_dev_val_candidates": len(functional_dev_val),
        "functional_dev_fit_uids": functional_dev_fit,
        "functional_dev_val_uids": functional_dev_val,
        "payload_files_opened": 0,
        "allowlist_sha256": pipeline.digest(allowlist),
        "boundary_sha256": pipeline.digest(boundary),
    }
    return {"allowlist": allowlist, "boundary": boundary, "audit": audit}


class AllowlistDatasetAdapter:
    """Provision authorized LeetCodeDataset rows only after frozen allowlist checks.

    Checks canonical dataset identity, allowlist membership, reservation-boundary
    non-membership, and (during target building) frozen development_fit assignment
    before parsing signatures, statements or tests. Reference solutions are
    stripped immediately and never stored or returned.
    """

    def __init__(
        self,
        dataset_path: Path,
        *,
        allowlist: dict,
        boundary: dict,
        authorization: dict,
        plan: dict | None = None,
        verify_canonical_file: bool = True,
    ):
        if not isinstance(authorization, dict) or authorization.get("authorized") is not True:
            raise PermissionError("Dataset provisioning requires explicit owner authorization")
        _nonempty_str(authorization.get("authority"), "authorization.authority")
        _nonempty_str(authorization.get("scope"), "authorization.scope")

        self.allowlist = pipeline._validate_allowlist(allowlist)
        if set(boundary) != {"uids", "keys", "families", "structural_groups", "sources_sha256"}:
            raise ValueError("Incomplete reservation boundary")
        self.boundary = copy.deepcopy(boundary)
        self._allowed_uids = frozenset(self.allowlist["uids"])
        self._allowed_keys = frozenset(self.allowlist["keys"])
        self._blocked_uids = frozenset(self.boundary["uids"])
        self._blocked_keys = frozenset(self.boundary["keys"])
        self._blocked_families = frozenset(self.boundary["families"])

        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.is_file():
            raise FileNotFoundError(f"Dataset file absent: {self.dataset_path}")
        self.fixture_mode = not verify_canonical_file
        if verify_canonical_file:
            self.file_receipt = verify_pinned_download(self.dataset_path, FILES["LeetCodeDataset-train.jsonl"])
        else:
            self.file_receipt = {
                "bytes": self.dataset_path.stat().st_size,
                "sha256": _sha256_file(self.dataset_path),
                "identity": "unit-test-fixture",
            }

        self.plan: dict | None = None
        self._plan_splits: dict[str, str] = {}
        if plan is not None:
            self.bind_plan(plan)

        # Retain only sanitized raw fields for rows passing both allowlist and boundary gates.
        self._sanitized_rows: dict[str, dict] = {}
        self.skipped_non_allowlisted = 0
        with self.dataset_path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                raw = json.loads(line)
                uid = f"lcd:{raw['question_id']}"
                slug = str(raw["task_id"])
                key = f"lc:{slug}"
                if not self._is_identity_permitted(uid, key, slug):
                    self.skipped_non_allowlisted += 1
                    continue
                if uid in self._sanitized_rows:
                    raise ValueError(f"Duplicate allowlisted UID in dataset: {uid}")
                # Strip completion/response immediately so reference solutions never reside in memory.
                self._sanitized_rows[uid] = {
                    "question_id": str(raw["question_id"]),
                    "task_id": slug,
                    "entry_point": str(raw["entry_point"]),
                    "starter_code": str(raw["starter_code"]),
                    "problem_description": str(raw["problem_description"]),
                    "test": str(raw["test"]),
                    "estimated_date": str(raw.get("estimated_date") or ""),
                    "difficulty": str(raw.get("difficulty") or ""),
                    "tags": list(raw.get("tags") or []),
                }

    def _is_identity_permitted(self, uid: str, key: str, slug: str) -> bool:
        if uid not in self._allowed_uids or key not in self._allowed_keys:
            return False
        if uid in self._blocked_uids or key in self._blocked_keys:
            return False
        if sibling_base(slug) in self._blocked_families:
            return False
        return True

    def _require_permitted_identity(self, uid: str, key: str) -> dict:
        slug = key.removeprefix("lc:")
        if not key.startswith("lc:") or not self._is_identity_permitted(uid, key, slug):
            raise PermissionError(f"Dataset access denied outside frozen allowlist/boundary: {uid} ({key})")
        if uid not in self._sanitized_rows:
            raise KeyError(f"Allowlisted problem absent from dataset file: {uid}")
        return self._sanitized_rows[uid]

    def bind_plan(self, plan: dict) -> None:
        validated = pipeline.validate_plan(plan)
        if validated.get("allowlist") != self.allowlist:
            raise PermissionError("Plan allowlist does not match adapter allowlist")
        if validated["boundary"] != self.boundary:
            raise PermissionError("Plan reservation boundary does not match adapter boundary")
        self.plan = validated
        self._plan_splits = {row["uid"]: row["split"] for row in validated["rows"]}

    def _parse_normalized_pair(self, raw: dict) -> tuple[Problem, list[dict]]:
        uid = f"lcd:{raw['question_id']}"
        slug = raw["task_id"]
        if "." not in raw["entry_point"]:
            raise ValueError(f"Unsupported entry_point on {uid}: {raw['entry_point']}")
        method = raw["entry_point"].split(".", 1)[1]
        try:
            params = values.signature(raw["starter_code"], method)
            ret_ann = values.return_annotation(raw["starter_code"], method)
        except values.Unsupported as exc:
            raise ValueError(f"Unsupported signature on {uid}: {exc}") from exc
        if ret_ann == "None":
            raise ValueError(f"In-place None-return problem unsupported on {uid}")
        public, public_dropped = importers.statement_examples(raw["problem_description"].strip(), params, ret_ann)
        if public_dropped or not public:
            raise ValueError(f"Incomplete or missing parseable public examples on {uid}")
        hidden, hidden_dropped = importers.lcd_hidden_tests(raw["test"], params)
        if hidden_dropped != 0 or not hidden:
            raise ValueError(f"Incomplete or missing parseable independent tests on {uid}")
        problem = Problem(
            uid=uid,
            source="lcd",
            source_id=raw["question_id"],
            title=slug.replace("-", " "),
            slug=slug,
            statement=raw["problem_description"].strip(),
            io_mode="functional",
            starter_code=raw["starter_code"],
            entry={"class": "Solution", "method": method},
            params=[list(p) for p in params],
            date=raw["estimated_date"],
            difficulty=raw["difficulty"],
            tags=list(raw["tags"]),
            license=importers.LCD_LICENSE,
            attribution=f"https://leetcode.com/problems/{slug}/ via newfacade/LeetCodeDataset",
            evidence_ceiling=INDEPENDENT,
            reference_solutions=[],
            public_tests=public,
            hidden_tests_path="",
            import_notes={
                "lcd_split": "train",
                "reference_stripped": True,
                "fixture_mode": self.fixture_mode,
            },
        )
        corrected_hidden = test_corrections.apply(problem, hidden)
        return problem, corrected_hidden

    def extract_allowlisted_metadata_hashes(
        self,
        family_by_uid: dict[str, str],
        *,
        structural_groups_by_uid: dict[str, list[str]] | None = None,
        aliases_by_uid: dict[str, list[str]] | None = None,
    ) -> tuple[list[dict], dict[str, str]]:
        """Build identity-only metadata and hashes strictly over allowlisted rows.

        Returns ``(metadata_rows, unusable_by_uid)`` without exposing problem
        statements, starter code, reference solutions or test cases.
        """
        structural_groups_by_uid = structural_groups_by_uid or {}
        aliases_by_uid = aliases_by_uid or {}
        metadata_rows = []
        unusable_by_uid = {}
        for uid, family in sorted(family_by_uid.items()):
            _nonempty_str(family, "family")
            if uid not in self._allowed_uids or uid in self._blocked_uids:
                raise PermissionError(f"Metadata hash extraction denied for non-allowlisted UID: {uid}")
            if uid not in self._sanitized_rows:
                unusable_by_uid[uid] = "absent_from_lcd_train"
                continue
            raw = self._sanitized_rows[uid]
            key = "lc:" + raw["task_id"]
            self._require_permitted_identity(uid, key)
            try:
                problem, independent_tests = self._parse_normalized_pair(raw)
            except ValueError as exc:
                unusable_by_uid[uid] = str(exc)
                continue
            nid = int(raw["question_id"])
            default_aliases = [f"leetcode:{nid}", f"doocs:{nid:04d}"]
            extra_aliases = list(aliases_by_uid.get(uid, ()))
            metadata_rows.append({
                "uid": uid,
                "key": key,
                "family": family,
                "aliases": sorted(set(default_aliases + extra_aliases)),
                "structural_groups": sorted(set(structural_groups_by_uid.get(uid, ()))),
                "problem_sha256": pipeline.digest(json.loads(problem.to_json())),
                "independent_tests_sha256": pipeline.digest(independent_tests),
            })
        return metadata_rows, unusable_by_uid

    def _require_development_fit_row(self, row: dict) -> dict:
        if self.plan is None:
            raise PermissionError("Adapter requires a bound frozen plan before payload or test loading")
        uid = _nonempty_str(row.get("uid"), "row.uid")
        key = _nonempty_str(row.get("key"), "row.key")
        raw = self._require_permitted_identity(uid, key)
        if self._plan_splits.get(uid) != "development_fit":
            raise PermissionError(f"Payload access denied for non-development_fit split ({self._plan_splits.get(uid)}): {uid}")
        return raw

    def load_problem(self, row: dict) -> Problem:
        raw = self._require_development_fit_row(row)
        problem, _ = self._parse_normalized_pair(raw)
        return problem

    def load_independent_tests(self, row: dict) -> list[dict]:
        raw = self._require_development_fit_row(row)
        _, independent_tests = self._parse_normalized_pair(raw)
        return independent_tests


class IsolatedTeacherAdapter:
    """Enforce separate teacher compute authorization and strict _public_input isolation."""

    REQUIRED_INPUT_FIELDS = frozenset({"statement", "starter_code", "params", "public_examples"})

    def __init__(self, generate_fn, *, authorization: dict):
        if not callable(generate_fn):
            raise TypeError("generate_fn must be callable")
        if not isinstance(authorization, dict) or authorization.get("authorized") is not True:
            raise PermissionError("Offline teacher inference requires separate explicit owner authorization")
        self.authority = _nonempty_str(authorization.get("authority"), "authorization.authority")
        self.model_id = _nonempty_str(authorization.get("model_id"), "authorization.model_id")
        self.model_revision = _nonempty_str(authorization.get("model_revision"), "authorization.model_revision")
        self.prompt_sha256 = pipeline._hash(authorization.get("prompt_sha256"))
        max_proposals = authorization.get("max_proposals", 4)
        if type(max_proposals) is not int or not 1 <= max_proposals <= 32:
            raise ValueError("authorization.max_proposals must be an int between 1 and 32")
        self.max_proposals = max_proposals
        self._generate_fn = generate_fn

    @property
    def teacher_identity(self) -> str:
        return f"{self.model_id}@{self.model_revision}#prompt:{self.prompt_sha256[:16]}"

    @classmethod
    def _verify_isolated_input(cls, public_input: dict) -> dict:
        if not isinstance(public_input, dict) or set(public_input) != cls.REQUIRED_INPUT_FIELDS:
            raise PermissionError("Teacher input must contain only statement, starter_code, params and public_examples")
        def walk_keys(node: object) -> None:
            if isinstance(node, dict):
                leaked = set(node) & FORBIDDEN_TEACHER_KEYS
                if leaked:
                    raise PermissionError(f"Forbidden reference/test/verdict field in teacher input: {sorted(leaked)}")
                for value in node.values():
                    walk_keys(value)
            elif isinstance(node, list):
                for item in node:
                    walk_keys(item)
        walk_keys(public_input)
        return copy.deepcopy(public_input)

    def propose(self, uid: str, public_input: dict, plan_sha256: str) -> list[dict]:
        _nonempty_str(uid, "uid")
        pipeline._hash(plan_sha256)
        isolated = self._verify_isolated_input(public_input)
        config = {
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "prompt_sha256": self.prompt_sha256,
            "max_proposals": self.max_proposals,
        }
        proposals = self._generate_fn(uid, isolated, plan_sha256, copy.deepcopy(config))
        if not isinstance(proposals, list) or not 1 <= len(proposals) <= self.max_proposals:
            raise ValueError(f"Teacher must return between 1 and {self.max_proposals} proposals")
        return copy.deepcopy(proposals)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-root", type=Path, default=LANE_ROOT)
    parser.add_argument("--write-allowlist", type=Path, default=None, help="New write-once allowlist JSON path")
    parser.add_argument("--write-boundary", type=Path, default=None, help="New write-once boundary JSON path")
    args = parser.parse_args()
    bundle = compile_committed_allowlist_and_boundary(args.lane_root)
    for target, payload in ((args.write_allowlist, bundle["allowlist"]), (args.write_boundary, bundle["boundary"])):
        if target is not None:
            with target.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(bundle["audit"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
