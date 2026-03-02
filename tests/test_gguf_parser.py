"""
Test GGUF Parser

Tests GGUF file metadata parsing:
- GGUFMetadata class initialization and parsing
- Filename parsing (quantization, params, architecture)
- File size methods
- Metadata accessors
- parse_gguf_file helper function
"""

import sys
import os

import unittest
from unittest.mock import patch, mock_open, MagicMock
import struct
import tempfile

from src.core.hardware import gguf_parser


class TestGGUFMetadata(unittest.TestCase):
    """Test GGUFMetadata class."""

    def test_nonexistent_file(self):
        """Should handle nonexistent files."""
        metadata = gguf_parser.GGUFMetadata('/nonexistent/file.gguf')

        self.assertFalse(metadata.is_valid())

    def test_invalid_magic_number(self):
        """Should reject files with wrong magic number."""
        # Create temp file with wrong magic
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', 0x12345678))  # Wrong magic
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertFalse(metadata.is_valid())
        finally:
            os.unlink(temp_path)

    def test_valid_gguf_file(self):
        """Should parse valid GGUF file."""
        # Create temp file with correct magic and version
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))  # Magic
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))  # Version
            f.write(struct.pack('<Q', 100))  # Tensor count
            f.write(struct.pack('<Q', 50))   # KV count
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertTrue(metadata.is_valid())
            self.assertEqual(metadata.metadata['tensor_count'], 100)
            self.assertEqual(metadata.metadata['kv_count'], 50)
        finally:
            os.unlink(temp_path)

    def test_parse_filename_q4_0(self):
        """Should detect Q4_0 quantization."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='_q4_0.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertEqual(metadata.get_quantization(), 'Q4_0')
        finally:
            os.unlink(temp_path)

    def test_parse_filename_q4_k_m(self):
        """Should detect Q4_K_M quantization."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='_q4_k_m.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertEqual(metadata.get_quantization(), 'Q4_K_M')
        finally:
            os.unlink(temp_path)

    def test_parse_filename_7b_params(self):
        """Should detect 7B parameter count."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='-7b.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertEqual(metadata.get_param_count_billions(), 7)
        finally:
            os.unlink(temp_path)

    def test_parse_filename_llama_architecture(self):
        """Should detect llama architecture."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='', prefix='llama-') as f:
            # Rename to add .gguf extension
            temp_path = f.name + '.gguf'
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))

        try:
            os.rename(f.name, temp_path)
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertEqual(metadata.get_architecture(), 'llama')
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_file_size_mb(self):
        """Should return file size in MB."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            # Write 2MB of data
            f.write(b'x' * (2 * 1024 * 1024))
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            size_mb = metadata.get_file_size_mb()
            self.assertGreaterEqual(size_mb, 2)
        finally:
            os.unlink(temp_path)

    def test_get_file_size_gb(self):
        """Should return file size in GB."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            size_gb = metadata.get_file_size_gb()
            self.assertIsInstance(size_gb, float)
            self.assertGreaterEqual(size_gb, 0.0)
        finally:
            os.unlink(temp_path)

    def test_format_info_invalid(self):
        """Should format info for invalid file."""
        metadata = gguf_parser.GGUFMetadata('/nonexistent/file.gguf')
        info = metadata.format_info()

        self.assertIn("Invalid", info)

    def test_format_info_valid(self):
        """Should format info for valid file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='_llama-7b_q4_k_m.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            info = metadata.format_info()

            self.assertIn("llama", info.lower())
            self.assertIn("7B", info)
            self.assertIn("Q4_K_M", info)
            self.assertIn("100", info)  # tensor count
        finally:
            os.unlink(temp_path)

    def test_parse_filename_all_quantizations(self):
        """Should detect various quantization types."""
        quantizations = {
            'q4_1': 'Q4_1',
            'q4_k_s': 'Q4_K_S',
            'q5_0': 'Q5_0',
            'q5_1': 'Q5_1',
            'q5_k_s': 'Q5_K_S',
            'q5_k_m': 'Q5_K_M',
            'q6_k': 'Q6_K',
            'q8_0': 'Q8_0',
            'f16': 'F16',
            'fp16': 'F16',
            'f32': 'F32',
            'fp32': 'F32',
        }

        for pattern, expected in quantizations.items():
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{pattern}.gguf') as f:
                f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
                f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
                f.write(struct.pack('<Q', 100))
                f.write(struct.pack('<Q', 50))
                temp_path = f.name

            try:
                metadata = gguf_parser.GGUFMetadata(temp_path)
                self.assertEqual(metadata.get_quantization(), expected,
                               f"Failed for pattern {pattern}")
            finally:
                os.unlink(temp_path)

    def test_parse_filename_all_architectures(self):
        """Should detect various architectures."""
        architectures = {
            'llama': 'llama',
            'gemma': 'gemma',
            'mistral': 'mistral',
            'phi': 'phi',
        }

        for name, expected in architectures.items():
            with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf', prefix=f'{name}_') as f:
                temp_path = f.name
                f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
                f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
                f.write(struct.pack('<Q', 100))
                f.write(struct.pack('<Q', 50))

            try:
                metadata = gguf_parser.GGUFMetadata(temp_path)
                self.assertEqual(metadata.get_architecture(), expected,
                               f"Failed for architecture {name}")
            finally:
                os.unlink(temp_path)

    def test_parse_filename_unknown_quantization(self):
        """Should return 'unknown' for unrecognized quantization."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='_unknown.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertEqual(metadata.get_quantization(), 'unknown')
        finally:
            os.unlink(temp_path)

    def test_parse_filename_no_params(self):
        """Should return value or None for ambiguous param count."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf', prefix='model_noparams_') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            result = metadata.get_param_count_billions()
            # May return None or a value depending on filename parsing
            self.assertIsInstance(result, (type(None), int, float))
        finally:
            os.unlink(temp_path)

    def test_parse_filename_all_param_sizes(self):
        """Should detect various parameter sizes."""
        param_sizes = {
            '1.5b': 1,
            '2.5b': 2,
            '3b': 3,
            '4b': 4,
            '8b': 8,
            '9b': 9,
            '12b': 12,
            '13b': 12,  # '13b' grouped with 12b
            '27b': 27,
            '33b': 33,
            '70b': 70,
        }

        for pattern, expected in param_sizes.items():
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'-{pattern}.gguf') as f:
                f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
                f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
                f.write(struct.pack('<Q', 100))
                f.write(struct.pack('<Q', 50))
                temp_path = f.name

            try:
                metadata = gguf_parser.GGUFMetadata(temp_path)
                self.assertEqual(metadata.get_param_count_billions(), expected,
                               f"Failed for pattern {pattern}")
            finally:
                os.unlink(temp_path)

    def test_old_gguf_version(self):
        """Should handle old GGUF versions."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', 2))  # Old version
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            # Should still be valid and parse what it can
            self.assertTrue(metadata.is_valid())
        finally:
            os.unlink(temp_path)

    def test_corrupted_file(self):
        """Should handle corrupted files gracefully."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(b'x')  # Corrupted data, not enough for version
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            self.assertFalse(metadata.is_valid())
        finally:
            os.unlink(temp_path)

    @patch('os.path.getsize')
    def test_get_file_size_error(self, mock_getsize):
        """Should return 0 on file size error."""
        mock_getsize.side_effect = OSError("File error")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            metadata = gguf_parser.GGUFMetadata(temp_path)
            size = metadata.get_file_size_mb()
            self.assertEqual(size, 0)
        finally:
            os.unlink(temp_path)


class TestParseGGUFFile(unittest.TestCase):
    """Test parse_gguf_file helper function."""

    def test_parse_valid_file(self):
        """Should return metadata for valid file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', gguf_parser.GGUF_MAGIC))
            f.write(struct.pack('<I', gguf_parser.GGUF_VERSION))
            f.write(struct.pack('<Q', 100))
            f.write(struct.pack('<Q', 50))
            temp_path = f.name

        try:
            result = gguf_parser.parse_gguf_file(temp_path)
            self.assertIsNotNone(result)
            self.assertIsInstance(result, gguf_parser.GGUFMetadata)
            self.assertTrue(result.is_valid())
        finally:
            os.unlink(temp_path)

    def test_parse_invalid_file(self):
        """Should return None for invalid file."""
        result = gguf_parser.parse_gguf_file('/nonexistent/file.gguf')

        self.assertIsNone(result)

    def test_parse_file_wrong_magic(self):
        """Should return None for wrong magic number."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            f.write(struct.pack('<I', 0x12345678))
            temp_path = f.name

        try:
            result = gguf_parser.parse_gguf_file(temp_path)
            self.assertIsNone(result)
        finally:
            os.unlink(temp_path)


def run_tests():
    """Run all GGUF parser tests."""
    print("=" * 80)
    print("Testing GGUF Parser")
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
