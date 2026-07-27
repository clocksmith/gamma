#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROGRAMS = ROOT / "projects" / "enwiki9" / "programs"
PARENT = (
    "cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_"
    "fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_"
    "bufthirtysecond_minmaps_v1"
)
CASES = {
    (
        "cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_"
        "fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_"
        "bufthirtysecond_minmaps_v1"
    ): {
        "CMIX_FXCM_CMC2_TIGHT": "1",
    },
    (
        "cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_"
        "densebudget96_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_"
        "bufthirtysecond_minmaps_v1"
    ): {
        "CMIX_FXCM_CMC2_TIGHT": "1",
        "CMIX_FXCM_CMC2_DENSE_RANGE": "1",
        "CMIX_FXCM_CMC2_DENSE_BUDGET_CELL_BYTES": "96",
    },
    (
        "cmix21_text_mmap_paq5_ppmd129552k_fxcmassoc10tight92_"
        "fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_"
        "bufthirtysecond_minmaps_v1"
    ): {
        "CMIX_PPMD_MEMORY_MB": "127",
        "CMIX_PPMD_MEMORY_KB": "129552",
        "CMIX_FXCM_CMC2_TIGHT": "1",
    },
    (
        "cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_"
        "fxcmidx13full_fxcmrcm20_ppmdguard2_rcm32_"
        "bufthirtysecond_minmaps_v1"
    ): {
        "CMIX_FXCM_CMC2_IDX13_DIV": "1",
        "CMIX_FXCM_CMC2_TIGHT": "1",
    },
}


def define_map(candidate: str) -> dict[str, str]:
    meta = json.loads((PROGRAMS / candidate / "meta.json").read_text())
    result: dict[str, str] = {}
    for item in meta["source"]["defines"]:
        assert item.startswith("-D") and "=" in item
        name, value = item[2:].split("=", 1)
        assert name not in result
        result[name] = value
    return result


def main() -> None:
    parent = define_map(PARENT)
    rows = []
    for candidate, overrides in CASES.items():
        child = define_map(candidate)
        expected = dict(parent)
        expected.update(overrides)
        assert child == expected
        rows.append(
            {
                "candidate": candidate,
                "define_count": len(child),
                "overrides": overrides,
                "exact_parent_plus_overrides": True,
            }
        )
    print(
        json.dumps(
            {
                "schema": "cmix21_parent_define_inheritance_receipt_v1",
                "parent": PARENT,
                "parent_define_count": len(parent),
                "candidates": rows,
                "verified": True,
                "score_credit_bytes": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
