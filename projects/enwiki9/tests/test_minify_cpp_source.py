from __future__ import annotations

from pathlib import Path

from projects.enwiki9.tools.minify_cpp_source import minify_tree, strip_comments


def test_strip_comments_preserves_literals_tokens_and_lines() -> None:
    source = (
        'const char* url = "https://example.test/a/*b*/"; // line comment\n'
        "int joined = left/**/right; /* block\ncomment */ int value = 3;\n"
        'const char* raw = R"tag(// not a comment\n/* neither */)tag";\n'
        "char slash = '/';\n"
    )
    result = strip_comments(source)

    assert result.count("\n") == source.count("\n")
    assert '"https://example.test/a/*b*/"' in result
    assert "left right" in result
    assert "line comment" not in result
    assert "block" not in result
    assert "comment */" not in result
    assert 'R"tag(// not a comment\n/* neither */)tag"' in result


def test_minify_tree_copies_non_cpp_files(tmp_path: Path) -> None:
    root = tmp_path / "source"
    output = tmp_path / "output"
    root.mkdir()
    (root / "main.cpp").write_text("int main() { return 0; } // remove\n")
    (root / "data.bin").write_bytes(b"a//b\x00")
    file_list = tmp_path / "files.list"
    file_list.write_text("main.cpp\ndata.bin\n")

    result = minify_tree(root, file_list, output)

    assert result["files"] == 2
    assert result["transformed_files"] == 1
    assert result["source_bytes_removed"] > 0
    assert "remove" not in (output / "main.cpp").read_text()
    assert (output / "data.bin").read_bytes() == b"a//b\x00"
