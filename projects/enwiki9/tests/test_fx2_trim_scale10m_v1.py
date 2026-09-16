"""Exercise the frozen ZIP-admission cases against the scale runner."""
from unittest.mock import patch

from tests.test_fx2_trim_confirm1m_v1 import Tests as SourceCases
from tools import fx2_trim_scale10m_v1 as candidate


class Tests(SourceCases):
    def setUp(self):
        for name in ('members', 'source_zip', 'ROOT'):
            active = patch('tests.test_fx2_trim_confirm1m_v1.' + name,
                           getattr(candidate, name))
            active.start()
            self.addCleanup(active.stop)


del SourceCases
