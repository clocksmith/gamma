from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import pytest

from gamma_enwiki9.evidence.artifacts import append_canonical_event, canonical_bytes, publish_immutable_artifact
from gamma_enwiki9.packaging.candidates import codec_entrypoint, scaffold_spec
from gamma_enwiki9.research.transactions import begin, reconcile, require_committed


def test_canonical_serialization_preserves_v1_identity():
    assert canonical_bytes({"z": 1, "a": "café"}) == b'{"a":"caf\xc3\xa9","z":1}'
    with pytest.raises(ValueError):
        canonical_bytes({"x": float("nan")})


def test_immutable_publish_never_replaces_conflicting_bytes(tmp_path):
    path = tmp_path / "evidence"
    publish_immutable_artifact(path, b"original")
    publish_immutable_artifact(path, b"original")
    with pytest.raises(ValueError):
        publish_immutable_artifact(path, b"replacement")
    assert path.read_bytes() == b"original"


def test_concurrent_canonical_events_are_idempotent(tmp_path):
    path = tmp_path / "events.jsonl"
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i: append_canonical_event(path, {"value": i % 3}, event_id=str(i % 3)), range(18)))
    assert len(path.read_text().splitlines()) == 3
    with path.open("ab") as stream:
        stream.write(b'{"incomplete":')
    with pytest.raises(ValueError, match="incomplete tail"):
        append_canonical_event(path, {"next": 1})


def test_transaction_recovers_after_event_append_before_marker(tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "program.py").write_text("source")
    begin(candidate, {"transaction_id": "creation"})
    events = tmp_path / "events.jsonl"
    calls = []
    def mutation(intent):
        append_canonical_event(events, {"candidate": "c"}, event_id=intent["transaction_id"])
        if not calls:
            calls.append("failed")
            raise OSError("injected after event publication")
    with pytest.raises(OSError):
        reconcile(candidate, revision=lambda i: None, mutation=mutation, register=lambda i: None)
    with pytest.raises(ValueError, match="incomplete"):
        require_committed(candidate)
    reconcile(candidate, revision=lambda i: pytest.fail("revision already committed"), mutation=mutation,
              register=lambda i: calls.append("registered"))
    require_committed(candidate)
    assert len(events.read_text().splitlines()) == 1
    assert calls == ["failed", "registered"]
    assert (candidate / "program.py").read_text() == "source"


def test_recipe_cannot_execute_as_codec(tmp_path):
    (tmp_path / "program.py").write_text('raise RuntimeError("must not execute")\n')
    spec = scaffold_spec(tmp_path, kind="experiment_recipe", codec={"candidate_id": "codec", "revision": "1" * 64})
    (tmp_path / "candidate.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="cannot run through the codec driver"):
        codec_entrypoint(tmp_path)


@pytest.mark.parametrize("kind,extra", [
    ("standalone_codec", {}), ("analysis_only", {}),
    ("experiment_recipe", {"codec": {"candidate_id": "codec", "revision": "a" * 64}}),
    ("external_adapter", {"upstream": {"sha256": "b" * 64}, "transformations": [{"preimage": "c" * 64, "postimage": "d" * 64}]}),
])
def test_candidate_kind_has_appropriate_explicit_entrypoint(tmp_path, kind, extra):
    (tmp_path / "program.py").write_text("def compress(data): return data\ndef decompress(data): return data\ndef main(): pass\n")
    spec = scaffold_spec(tmp_path, kind=kind, **extra)
    assert spec["kind"] == kind
    assert spec["sources"][0]["path"] == "program.py"
    if kind == "standalone_codec":
        assert spec["entrypoint"]["compress"] == "compress"
    else:
        assert spec["entrypoint"]["callable"] == "main"


def test_lab_creation_recovers_without_removing_source(tmp_path, monkeypatch):
    import enwiki9_lab as lab
    monkeypatch.setattr(lab, "ROOT", tmp_path)
    monkeypatch.setattr(lab, "PROGRAMS", tmp_path / "programs")
    monkeypatch.setattr(lab, "MUTATION_LOG", tmp_path / "operations/mutations.jsonl")
    monkeypatch.setattr(lab.candidate_revisions, "record_revision", lambda **kwargs: None)
    attempts = []
    def register(cid):
        if not attempts:
            attempts.append("failed")
            raise OSError("index publication interrupted")
        attempts.append(cid)
    monkeypatch.setattr(lab, "register_candidate", register)
    with pytest.raises(OSError):
        lab.create_candidate(candidate_id="fixture", parent=None, hypothesis="test", description=None, replacements=[])
    source = tmp_path / "programs/fixture/program.py"
    assert source.is_file()
    with pytest.raises(ValueError, match="incomplete"):
        lab.candidate_meta("fixture")
    lab.reconcile_candidate_creation("fixture")
    assert lab.candidate_meta("fixture")["kind"] == "standalone_codec"
    assert len(lab.MUTATION_LOG.read_text().splitlines()) == 1


def test_driver_uses_declared_nested_codec_entrypoint(tmp_path, monkeypatch):
    import sys
    project = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project))
    from lib import driver
    candidate = tmp_path / "programs/example"
    (candidate / "codec").mkdir(parents=True)
    source = candidate / "codec/implementation.py"
    source.write_text("def compress(data): return data[::-1]\ndef decompress(data): return data[::-1]\n")
    spec = scaffold_spec(candidate, kind="standalone_codec", entrypoint="codec/implementation.py")
    (candidate / "candidate.json").write_text(json.dumps(spec))
    (candidate / "meta.json").write_text(json.dumps({"id": "example"}))
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    module, loaded = driver._load("example")
    assert loaded == source
    assert module.decompress(module.compress(b"fixture")) == b"fixture"
    # Freeze paths remain relative to the candidate root, not entrypoint's folder.
    monkeypatch.setattr(driver, "_comparison_source_closure", lambda source, candidate_root: [source])
    output = tmp_path / "output"
    output.mkdir()
    frozen = driver._freeze_comparison_build("example", source, output)
    assert frozen["source"].relative_to(frozen["root"]).as_posix() == "projects/enwiki9/programs/example/codec/implementation.py"
    assert frozen["source"].read_bytes() == source.read_bytes()
