"""Pytest bootstrap and shared fixtures for GAMMA tests."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT_STR = str(REPO_ROOT)
if REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, REPO_ROOT_STR)

TESTS_DIR = Path(__file__).resolve().parent

# Test files here that exercise the archived projects/enwiki9 lane. They get
# the `enwiki9` marker and a bare run deselects them; they still run with
# `-m enwiki9`, with GAMMA_ALL_TESTS=1, or when the file is named explicitly.
ENWIKI9_ARCHIVED_TEST_FILES = frozenset(
    {
        "test_build_cmix21_p1_matched_trace.py",
        "test_build_reproducible_source_shar.py",
        "test_build_reproducible_source_zip.py",
        "test_candidate_audit.py",
        "test_clockwork_candidate_gate.py",
        "test_clockwork_contracts.py",
        "test_cmix21_gate_decider.py",
        "test_cmix_aux_logit_blend_screen.py",
        "test_endpoint428_paired_trace.py",
        "test_enwiki9_status_receipt_speedlab.py",
        "test_fx2_attribution_external_base_screen.py",
        "test_fx2_cmix21_affine_endpoint_screen.py",
        "test_fx2_cmix21_contextual_endpoint_screen.py",
        "test_fx2_cmix21_nested_endpoint_screen.py",
        "test_p1_wrt_to_fx2pt_trace.py",
        "test_run_fx2_cmix21_backend_identity_screen.py",
        "test_run_fx2_cmix21_wrapper_proof.py",
        "test_seal_cmix21_lstm200_fx2lite428_10m_codec_failure.py",
        "test_seal_cmix21_lstm200_fx2lite428_10m.py",
        "test_seal_cmix21_lstm200_fx2lite428_native.py",
        "test_seal_cmix21_lstm200_fx2lite428_ppmd_recovery.py",
        "test_seal_cmix21_lstm200_fx2lite428_ram_recovery.py",
        "test_seal_fx2_cmix21_backend_identity_runtime_screen.py",
        "test_seal_fx2_cmix21_lstm112_plus80_10m_receipt.py",
        "test_seal_fx2_cmix21_lstm112_plus80_terminal.py",
        "test_seal_fx2_cmix21_lstm200_disjoint.py",
        "test_seal_fx2_cmix21_lstm200_source_frontier.py",
        "test_seal_fx2_cmix21_matched_disjoint.py",
        "test_seal_fx2_cmix21_original_order_blend.py",
        "test_seal_fx2_cmix21_source_package_accounting.py",
        "test_seal_reproducible_source_shar_package.py",
        "test_seal_wikiir_target_backend_probe.py",
        "test_seal_wrt_static_boundary_swap_112plus80_gate.py",
        "test_seal_wrt_static_boundary_swap_disjoint.py",
        "test_seal_wrt_static_boundary_swap_geometry_title_proxy.py",
        "test_streaming_retrieval_receipt_audit.py",
        "test_wikiir_materialize.py",
        "test_wikiir_prior_page_columnar_probe.py",
        "test_wikiir_prior_page_delta_v1.py",
        "test_wikiir_template_grammar_v1.py",
        "test_wikiir_title_vertex_tail_layout.py",
        "test_wikiir_title_vertex_twopass_v1.py",
        "test_wikiir_title_vertex_v1.py",
        "test_wikiir_webgraph_v1.py",
        "test_wrt_entity_regret_router_shadow.py",
        "test_wrt_entity_trie_fx2_shadow.py",
        "test_wrt_sequence_memoizer_trace.py",
    }
)


def _explicit_test_files(config):
    files = set()
    for arg in config.args:
        path = Path(str(arg).split("::", 1)[0])
        if path.suffix == ".py":
            files.add(path.resolve())
    return files


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Mark archived enwiki9 tests and drop them from bare runs."""
    archived = []
    for item in items:
        path = Path(str(item.path))
        if path.parent == TESTS_DIR and path.name in ENWIKI9_ARCHIVED_TEST_FILES:
            item.add_marker(pytest.mark.enwiki9)
            archived.append(item)
    if not archived or config.getoption("markexpr") or os.environ.get("GAMMA_ALL_TESTS") == "1":
        return
    explicit = _explicit_test_files(config)
    drop = [item for item in archived if Path(str(item.path)).resolve() not in explicit]
    if drop:
        dropped = set(map(id, drop))
        config.hook.pytest_deselected(items=drop)
        items[:] = [item for item in items if id(item) not in dropped]
