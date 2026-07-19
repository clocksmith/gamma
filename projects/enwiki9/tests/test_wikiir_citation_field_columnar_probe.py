from projects.enwiki9.tools.wikiir_citation_field_columnar_probe import (
    cite_template_ranges,
    decode_transform,
    encode_transform,
    selected_value_spans,
)


SAMPLE = (
    b"before <ref>{{cite web |title=An [[Exact|example]] |url=https://x.test/a|"
    b"date=2026-07-18|author=A. Person}}</ref> after"
)


def test_detects_complete_citation_template() -> None:
    ranges = cite_template_ranges(SAMPLE)
    assert len(ranges) == 1
    spans = selected_value_spans(
        SAMPLE, (b"title", b"url", b"date", b"author")
    )
    assert [SAMPLE[start:end] for start, end, _ in spans] == [
        b"An [[Exact|example]] ",
        b"https://x.test/a",
        b"2026-07-18",
        b"A. Person",
    ]


def test_semantic_and_control_transforms_roundtrip() -> None:
    for mode in ("semantic", "ordinal_control"):
        payload = encode_transform(SAMPLE, "all", mode)
        assert decode_transform(payload) == SAMPLE


def test_incomplete_template_remains_literal() -> None:
    sample = b"x {{cite web|title=unfinished"
    payload = encode_transform(sample, "all", "semantic")
    assert decode_transform(payload) == sample
