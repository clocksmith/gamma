#!/usr/bin/env python3
"""Deterministic Wikipedia self-annotation graph for TESSERA QH0."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable

from causal_state_screen import WikiState


ROLE_NAMES = (
    "OUTSIDE",
    "PAGE_TITLE",
    "SECTION_HEADING",
    "PROSE_WORD",
    "LINK_TARGET",
    "LINK_LABEL",
    "TEMPLATE_NAME",
    "TEMPLATE_KEY",
    "TEMPLATE_VALUE",
    "CATEGORY",
    "REFERENCE_FIELD",
    "URL",
    "DATE",
    "NUMBER",
    "MEASUREMENT",
    "TABLE_CELL",
    "LIST_ITEM",
)
ROLE_IDS = {name: index for index, name in enumerate(ROLE_NAMES)}

RELATIONS = (
    "PAGE_TITLE",
    "LINK_TARGET",
    "LINK_LABEL",
    "TEMPLATE_NAME",
    "TEMPLATE_KEY",
    "CATEGORY",
    "SECTION_HEADING",
    "REFERENCE_FIELD",
    "LEAD",
    "TITLE_LEAD",
    "DATE_SHAPE",
    "URL_SHAPE",
    "UNIT_SHAPE",
)
RELATION_BITS = {name: 1 << index for index, name in enumerate(RELATIONS)}

WORD_RE = re.compile(rb"[A-Za-z][A-Za-z0-9_-]*")
TITLE_RE = re.compile(rb"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
TEXT_RE = re.compile(
    rb"<text(?:\s+[^>]*)?>(.*?)</text>", re.DOTALL | re.IGNORECASE
)
LINK_RE = re.compile(rb"\[\[([^\]\n]+)\]\]")
TEMPLATE_RE = re.compile(rb"\{\{([^{}\n]+)\}\}")
HEADING_RE = re.compile(rb"(?m)^={2,6}\s*(.*?)\s*={2,6}\s*$")
REF_OPEN_RE = re.compile(rb"<ref\b([^>]*)>", re.IGNORECASE)
ATTRIBUTE_RE = re.compile(rb"([A-Za-z_:][A-Za-z0-9_.:-]*)\s*=")
URL_RE = re.compile(rb"https?://[^\s<>\]\[{}|]+", re.IGNORECASE)
DATE_RE = re.compile(rb"\b(?:1[0-9]{3}|20[0-9]{2})(?:-[0-9]{2}-[0-9]{2})?\b")
UNIT_RE = re.compile(
    rb"\b(?:km|cm|mm|kg|mg|hz|mhz|ghz|miles?|feet|ft|meters?|metres?|percent)\b",
    re.IGNORECASE,
)


def canonical_lexeme(decoded: bytes) -> str:
    return decoded.decode("latin-1").lower()


def words(data: bytes) -> tuple[str, ...]:
    return tuple(match.group(0).decode("ascii").lower() for match in WORD_RE.finditer(data))


def add_relation(target: dict[str, int], data: bytes, relation: str) -> None:
    bit = RELATION_BITS[relation]
    for word in words(data):
        target[word] = target.get(word, 0) | bit


def build_self_annotation_signatures(pages: Iterable[bytes]) -> dict[str, int]:
    signatures: dict[str, int] = {}
    for page in pages:
        title_match = TITLE_RE.search(page)
        text_match = TEXT_RE.search(page)
        title = title_match.group(1) if title_match else b""
        text = text_match.group(1) if text_match else b""
        add_relation(signatures, title, "PAGE_TITLE")

        for match in LINK_RE.finditer(text):
            fields = match.group(1).split(b"|", 1)
            target = fields[0]
            relation = "CATEGORY" if target.lower().startswith(b"category:") else "LINK_TARGET"
            add_relation(signatures, target, relation)
            if len(fields) == 2:
                add_relation(signatures, fields[1], "LINK_LABEL")

        for match in TEMPLATE_RE.finditer(text):
            fields = match.group(1).split(b"|")
            if fields:
                add_relation(signatures, fields[0], "TEMPLATE_NAME")
            for field in fields[1:]:
                if b"=" in field:
                    key, _ = field.split(b"=", 1)
                    add_relation(signatures, key, "TEMPLATE_KEY")

        for match in HEADING_RE.finditer(text):
            add_relation(signatures, match.group(1), "SECTION_HEADING")
        for match in REF_OPEN_RE.finditer(text):
            for attribute in ATTRIBUTE_RE.finditer(match.group(1)):
                add_relation(signatures, attribute.group(1), "REFERENCE_FIELD")

        lead = re.split(
            rb"\n\s*\n|^={2,6}", text, maxsplit=1, flags=re.MULTILINE
        )[0]
        add_relation(signatures, lead, "LEAD")
        title_words = set(words(title))
        lead_words = set(words(lead))
        for word in title_words & lead_words:
            signatures[word] = signatures.get(word, 0) | RELATION_BITS["TITLE_LEAD"]

        for match in URL_RE.finditer(text):
            add_relation(signatures, match.group(0), "URL_SHAPE")
        for match in DATE_RE.finditer(text):
            add_relation(signatures, match.group(0), "DATE_SHAPE")
        for match in UNIT_RE.finditer(text):
            add_relation(signatures, match.group(0), "UNIT_SHAPE")
    return dict(sorted(signatures.items()))


def morphology_class(lexeme: str) -> int:
    if not lexeme:
        return 0
    if lexeme.isdigit():
        return 1
    if lexeme.endswith("ing") and len(lexeme) > 4:
        return 2
    if lexeme.endswith("ed") and len(lexeme) > 3:
        return 3
    if lexeme.endswith("ly") and len(lexeme) > 3:
        return 4
    if lexeme.endswith("s") and len(lexeme) > 2:
        return 5
    if "-" in lexeme:
        return 6
    return 7


def surface_class(decoded: bytes) -> int:
    text = decoded.decode("latin-1")
    if not text:
        return 0
    if text.islower():
        return 1
    if text.isupper():
        return 2
    if text[:1].isupper() and text[1:].islower():
        return 3
    if text.isdigit():
        return 4
    return 5


def _line_prefix(tail: bytes) -> bytes:
    return tail.rsplit(b"\n", 1)[-1]


def role_id(state: WikiState) -> int:
    """Return the role visible before the next WRT event is decoded."""
    if state.field_id == 1:
        return ROLE_IDS["PAGE_TITLE"]
    if state.field_id == 3:
        return ROLE_IDS["DATE"]
    if state.field_id != 6:
        return ROLE_IDS["OUTSIDE"]

    tail = bytes(state.tail)
    lower = tail.lower()
    line = _line_prefix(lower)
    if state.slot == 1:
        return ROLE_IDS["CATEGORY"]
    if state.slot in (5, 6) or state.ref_depth:
        return ROLE_IDS["REFERENCE_FIELD"]
    if state.slot == 7 or re.search(rb"https?://[^\s]*$", lower):
        return ROLE_IDS["URL"]
    if state.mode == 1 or state.link_depth:
        segment = lower.rsplit(b"[[", 1)[-1]
        return ROLE_IDS["LINK_LABEL" if b"|" in segment else "LINK_TARGET"]
    if state.mode == 2 or state.template_depth:
        segment = lower.rsplit(b"{{", 1)[-1]
        if b"|" not in segment:
            return ROLE_IDS["TEMPLATE_NAME"]
        field = segment.rsplit(b"|", 1)[-1]
        return ROLE_IDS["TEMPLATE_VALUE" if b"=" in field else "TEMPLATE_KEY"]
    if state.mode == 4 or state.table_depth:
        return ROLE_IDS["TABLE_CELL"]
    stripped = line.lstrip()
    if stripped.startswith((b"*", b"#", b";", b":")):
        return ROLE_IDS["LIST_ITEM"]
    if line.startswith(b"==") and not re.search(rb"={2,6}\s*$", line[2:]):
        return ROLE_IDS["SECTION_HEADING"]
    return ROLE_IDS["PROSE_WORD"]


def relation_histogram(signatures: dict[str, int]) -> dict[str, int]:
    result = defaultdict(int)
    for signature in signatures.values():
        for name, bit in RELATION_BITS.items():
            if signature & bit:
                result[name] += 1
    return dict(sorted(result.items()))
