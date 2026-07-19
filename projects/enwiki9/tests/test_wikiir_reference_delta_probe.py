from projects.enwiki9.tools.wikiir_reference_delta_probe import (
    decode_transform,
    decode_inline_transform,
    encode_transform,
    encode_inline_transform,
    full_corpus_oracle,
    reference_body_spans,
)


SAMPLE = (
    b"prefix &lt;ref&gt;{{cite web|title=First title|date=2020}}&lt;/ref&gt; "
    b"middle &lt;ref&gt;{{cite web|title=Second title|date=2021}}&lt;/ref&gt; "
    b"&lt;ref name=alias/&gt; suffix"
)


def test_extracts_complete_nonselfclosing_reference_bodies() -> None:
    spans = reference_body_spans(SAMPLE)
    assert len(spans) == 2
    assert SAMPLE[spans[0][0] : spans[0][1]].startswith(b"{{cite web")


def test_literal_and_delta_modes_roundtrip() -> None:
    for mode in ("literal", "delta"):
        payload, metrics = encode_transform(SAMPLE, mode)
        assert metrics["reference_bodies"] == 2
        assert decode_transform(payload) == SAMPLE


def test_delta_selects_similar_prior_reference() -> None:
    payload, metrics = encode_transform(SAMPLE, "delta")
    assert decode_transform(payload) == SAMPLE
    assert metrics["paying_delta_events"] == 1
    assert metrics["raw_mdl_saved_bytes"] > 0


def test_inline_literal_and_delta_modes_roundtrip() -> None:
    for mode in ("literal", "delta"):
        payload, metrics = encode_inline_transform(SAMPLE, mode)
        assert metrics["reference_bodies"] == 2
        assert decode_inline_transform(payload) == SAMPLE


def test_full_corpus_oracle_is_causal_raw_mdl_only() -> None:
    oracle = full_corpus_oracle(SAMPLE)
    assert oracle["reference_bodies"] == 2
    assert oracle["paying_delta_events"] == 1
    assert oracle["raw_mdl_saved_bytes"] > 0
