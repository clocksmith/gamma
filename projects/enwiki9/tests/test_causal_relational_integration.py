"""Full sealed v2 parser/inverse/binding path on declared synthetic sequences."""
from pathlib import Path
import subprocess


def test_bidirectional_persistent_binding_with_uniform_parent(tmp_path):
    root = Path(__file__).resolve().parents[1]
    binary = tmp_path / 'relational-integration'
    subprocess.run([
        'g++', '-std=c++17', '-O1', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=undefined', '-fno-sanitize-recover=all', '-I', str(root / 'lib'),
        str(root / 'tests/causal_relational_integration_fixture.cpp'), '-o', str(binary),
    ], check=True, timeout=60)
    result = subprocess.run([str(binary)], check=True, capture_output=True,
                            text=True, timeout=15)
    rows = [line.split() for line in result.stdout.splitlines()]
    assert [row[0] for row in rows] == ['title-to-content', 'content-to-link']
    for row in rows:
        parent, bookkeeping, independent, shared, wrong = map(float, row[1:])
        assert parent == bookkeeping
        assert shared + 1 < min(parent, independent, wrong)
