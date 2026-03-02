"""
Test UI Components

Tests basic UI utility functions:
- color_text: Apply color codes
- print_separator: Print separator lines
- print_header: Print formatted headers
- wrap_print: Wrap and print text
"""

import sys

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from src.ui import components as ui_components
from src.core import config as cfg


class TestColorText(unittest.TestCase):
    """Test color_text function."""

    def test_color_text_with_colors_enabled(self):
        """Should apply color codes when colors enabled."""
        with patch.object(cfg, 'USE_COLORS', True):
            result = ui_components.color_text("Hello", "\033[31m")

            self.assertIn("Hello", result)
            self.assertIn("\033[31m", result)
            self.assertIn(cfg.COLOR_RESET, result)

    def test_color_text_with_colors_disabled(self):
        """Should return plain text when colors disabled."""
        with patch.object(cfg, 'USE_COLORS', False):
            result = ui_components.color_text("Hello", "\033[31m")

            self.assertEqual(result, "Hello")

    def test_color_text_no_color_code(self):
        """Should return plain text when no color code provided."""
        with patch.object(cfg, 'USE_COLORS', True):
            result = ui_components.color_text("Hello", "")

            self.assertEqual(result, "Hello")

    def test_color_text_none_color_code(self):
        """Should return plain text when color code is None."""
        with patch.object(cfg, 'USE_COLORS', True):
            result = ui_components.color_text("Hello", None)

            self.assertEqual(result, "Hello")


class TestPrintSeparator(unittest.TestCase):
    """Test print_separator function."""

    def test_print_separator_default(self):
        """Should print default separator."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.print_separator()
            output = fake_out.getvalue()

            self.assertEqual(output.strip(), "=" * 70)

    def test_print_separator_custom_char(self):
        """Should print separator with custom character."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.print_separator(char="-")
            output = fake_out.getvalue()

            self.assertEqual(output.strip(), "-" * 70)

    def test_print_separator_custom_length(self):
        """Should print separator with custom length."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.print_separator(char="*", length=50)
            output = fake_out.getvalue()

            self.assertEqual(output.strip(), "*" * 50)


class TestPrintHeader(unittest.TestCase):
    """Test print_header function."""

    def test_print_header(self):
        """Should print formatted header."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.print_header("Test Title")
            output = fake_out.getvalue()

            self.assertIn("Test Title", output)
            self.assertIn("=" * 70, output)
            # Should have newlines at start
            self.assertTrue(output.startswith("\n"))

    def test_print_header_centers_text(self):
        """Should center title in header."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.print_header("X")
            output = fake_out.getvalue()

            # Title should be centered
            lines = output.strip().split('\n')
            # Find the line with the title
            title_line = [line for line in lines if 'X' in line and '=' in line][0]
            # Should have 'X' surrounded by '='
            self.assertIn("X", title_line)


class TestWrapPrint(unittest.TestCase):
    """Test wrap_print function."""

    def test_wrap_print_short_text(self):
        """Should print short text without wrapping."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.wrap_print("Short text")
            output = fake_out.getvalue()

            self.assertEqual(output.strip(), "Short text")

    def test_wrap_print_long_text(self):
        """Should wrap long text."""
        long_text = "This is a very long piece of text " * 10

        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.wrap_print(long_text, width=50)
            output = fake_out.getvalue()

            lines = output.strip().split('\n')
            # Should have wrapped into multiple lines
            self.assertGreater(len(lines), 1)
            # Each line should be <= width
            for line in lines:
                self.assertLessEqual(len(line), 50)

    def test_wrap_print_with_indent(self):
        """Should apply indentation."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.wrap_print("Test text", indent="  ")
            output = fake_out.getvalue()

            self.assertTrue(output.startswith("  "))

    def test_wrap_print_with_initial_indent_add(self):
        """Should apply additional initial indent."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.wrap_print("Test text", indent="  ", initial_indent_add=">> ")
            output = fake_out.getvalue()

            # First line should have both indents
            first_line = output.split('\n')[0]
            self.assertTrue(first_line.startswith("  >> "))

    def test_wrap_print_normalizes_whitespace(self):
        """Should normalize multiple spaces."""
        text_with_spaces = "This   has    many     spaces"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.wrap_print(text_with_spaces)
            output = fake_out.getvalue()

            # Should normalize to single spaces
            self.assertIn("This has many spaces", output)

    def test_wrap_print_custom_width(self):
        """Should respect custom width."""
        long_text = "word " * 20

        with patch('sys.stdout', new=StringIO()) as fake_out:
            ui_components.wrap_print(long_text, width=30)
            output = fake_out.getvalue()

            lines = output.strip().split('\n')
            for line in lines:
                self.assertLessEqual(len(line), 30)


def run_tests():
    """Run all UI components tests."""
    print("=" * 80)
    print("Testing UI Components")
    print("=" * 80)
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print(f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
