from projects.enwiki9.tools.wikiir_named_ref_intern_probe import (
    decode_transform,
    encode_transform,
    full_corpus_census,
    named_ref_spans,
    skeleton_and_values,
)


SAMPLE = (
    b'<ref name="long-reference">first</ref> x <ref name="long-reference"/> '
    b"<ref name='other'>second</ref> <ref name=bare/> "
    b'&lt;ref name="escaped"&gt;third&lt;/ref&gt; '
    b'&lt;ref name="escaped"/&gt;'
)


def test_extracts_quoted_and_bare_reference_names() -> None:
    spans = named_ref_spans(SAMPLE)
    assert [SAMPLE[start:end] for start, end in spans] == [
        b"long-reference",
        b"long-reference",
        b"other",
        b"bare",
        b"escaped",
        b"escaped",
    ]


def test_literal_and_intern_modes_roundtrip() -> None:
    for mode in ("literal", "intern"):
        payload = encode_transform(SAMPLE, mode)
        assert decode_transform(payload) == SAMPLE


def test_intern_mode_removes_repeated_literal() -> None:
    literal = encode_transform(SAMPLE, "literal")
    intern = encode_transform(SAMPLE, "intern")
    _, values = skeleton_and_values(SAMPLE)
    assert len(values) == 6
    assert len(intern) < len(literal)


def test_full_corpus_census_counts_repeat_ceiling() -> None:
    census = full_corpus_census(SAMPLE)
    assert census["named_refs"] == 6
    assert census["repeat_occurrences"] == 2
    assert census["maximum_raw_intern_savings_before_container"] > 0
