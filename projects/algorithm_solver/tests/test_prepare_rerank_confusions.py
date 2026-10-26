import unittest

from algsolve.prepare_rerank_confusions import description


class DescriptionTests(unittest.TestCase):
    def test_numeric_superscripts_survive_html_removal(self):
        raw = b'<p>Return the count modulo 10<sup>9</sup> + 7, with tolerance 10<sup>-5</sup>.</p><p>Example 1:</p><pre>answer payload</pre>'
        self.assertEqual(description(raw), 'Return the count modulo 10^9 + 7, with tolerance 10^-5.')

    def test_decodes_entities_and_keeps_only_statement_description(self):
        raw = b'<p>Return values &lt; k &amp; keep the 2<sup>nd</sup> node.</p><strong>Example 1:</strong><pre>not candidate text</pre>'
        self.assertEqual(description(raw), 'Return values < k & keep the 2 nd node.')
        with self.assertRaises(ValueError):description(b'Incomplete statement snapshot')


if __name__ == '__main__':
    unittest.main()
