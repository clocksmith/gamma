import ast
from pathlib import Path


def test_latent_handoff_never_calls_legacy_switch_or_fallback_paths() -> None:
    root = Path("src/mind_meld/latent_handoff")
    prohibited_attributes = {
        "_replay_kv_cache",
        "_transfer_kv_cache",
        "reset_kv_cache",
        "bridge_kv_cache_to",
    }
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert not (used & prohibited_attributes), f"{path} references a prohibited route"
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module not in {
                    "src.mind_meld.core.meld_engine",
                    "src.mind_meld.bridges.kv_cache_handler",
                }
