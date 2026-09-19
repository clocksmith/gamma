from types import SimpleNamespace
import zlib

import pytest
from gamma_enwiki9.adapters.xml_history_comparison_v2 import native_module_identity


def test_builtin_and_extension_identity(tmp_path):
    built = SimpleNamespace(__name__='fixture', __spec__=SimpleNamespace(origin='built-in'))
    assert native_module_identity(built)['kind'] == 'built-in'
    extension = tmp_path / 'fixture.so'
    extension.write_bytes(b'synthetic native module')
    identity = native_module_identity(SimpleNamespace(__file__=str(extension)))
    assert identity['kind'] == 'extension'
    assert identity['artifact']['bytes'] == 23
    assert native_module_identity(zlib)['kind'] in ('built-in', 'extension')
    with pytest.raises(ValueError):
        native_module_identity(SimpleNamespace(__spec__=SimpleNamespace(origin='unknown')))
