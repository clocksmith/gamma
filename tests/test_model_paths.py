"""
Test Model Paths

Tests model path resolution and discovery:
- get_project_root: Project root detection
- resolve_model_path: Path resolution for various formats
- list_available_models: Model discovery
- setup_models_directory: Directory creation
- create_model_symlink: Symlink management
"""

import sys
import os

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.core.models import model_paths


class TestGetProjectRoot(unittest.TestCase):
    """Test get_project_root function."""

    def test_get_project_root(self):
        """Should return project root path."""
        root = model_paths.get_project_root()

        self.assertIsInstance(root, Path)
        # Should be a valid directory
        self.assertTrue(root.exists())
        self.assertTrue(root.is_dir())


class TestResolveModelPath(unittest.TestCase):
    """Test resolve_model_path function."""

    def test_huggingface_identifier(self):
        """Should return HuggingFace identifiers as-is."""
        identifiers = [
            "google/gemma-2b",
            "mistralai/mistral-7b",
            "meta-llama/llama-2-7b",
        ]

        for identifier in identifiers:
            result = model_paths.resolve_model_path(identifier)
            self.assertEqual(result, identifier)

    def test_local_path_with_slash_not_hf(self):
        """Should handle local paths that contain slashes."""
        # Path with dot in first part - not HF identifier
        result = model_paths.resolve_model_path("my.models/test.gguf")
        # Won't find the file, returns original
        self.assertEqual(result, "my.models/test.gguf")

    def test_absolute_path_exists(self):
        """Should return absolute path if it exists."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gguf') as f:
            temp_path = f.name

        try:
            result = model_paths.resolve_model_path(temp_path)
            self.assertEqual(result, temp_path)
        finally:
            os.unlink(temp_path)

    def test_absolute_path_not_exists(self):
        """Should return original if absolute path doesn't exist."""
        fake_path = "/nonexistent/model.gguf"
        result = model_paths.resolve_model_path(fake_path)

        # Should return original since it doesn't exist
        self.assertEqual(result, fake_path)

    def test_relative_path_exists(self):
        """Should convert relative path to absolute if it exists."""
        # Create temp file in current directory
        temp_file = "test_model_temp.gguf"
        with open(temp_file, 'w') as f:
            f.write("test")

        try:
            result = model_paths.resolve_model_path(temp_file)
            self.assertTrue(os.path.isabs(result))
            self.assertTrue(result.endswith(temp_file))
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_search_in_additional_paths(self):
        """Should search in additional paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = os.path.join(tmpdir, "model.gguf")
            with open(model_file, 'w') as f:
                f.write("test")

            result = model_paths.resolve_model_path(
                "model.gguf",
                additional_paths=[tmpdir]
            )

            self.assertEqual(result, os.path.abspath(model_file))

    def test_not_found_returns_original(self):
        """Should return original identifier if not found."""
        result = model_paths.resolve_model_path("nonexistent_model.gguf")
        self.assertEqual(result, "nonexistent_model.gguf")

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    def test_ollama_blobs_directory_search(self, mock_exists, mock_isdir, mock_listdir):
        """Should search in Ollama blobs directory."""
        # This is complex to test fully, but we can test the code path
        mock_isdir.return_value = True
        mock_exists.return_value = False
        mock_listdir.return_value = []  # Empty directory

        result = model_paths.resolve_model_path("model.gguf")
        # Won't find it, returns original
        self.assertEqual(result, "model.gguf")

    def test_ollama_blobs_direct_match(self):
        """Should find model in Ollama blobs directory with direct match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Ollama-like directory structure
            ollama_dir = os.path.join(tmpdir, "ollama")
            blobs_dir = os.path.join(ollama_dir, "blobs")
            os.makedirs(blobs_dir)

            # Create model file
            model_identifier = "sha256-abc123"
            model_file = os.path.join(blobs_dir, model_identifier)
            with open(model_file, 'w') as f:
                f.write("model")

            result = model_paths.resolve_model_path(
                model_identifier,
                additional_paths=[ollama_dir]
            )

            self.assertEqual(result, os.path.abspath(model_file))

    def test_ollama_blobs_partial_match(self):
        """Should find model in Ollama blobs directory with partial match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Ollama-like directory structure
            ollama_dir = os.path.join(tmpdir, "ollama")
            blobs_dir = os.path.join(ollama_dir, "blobs")
            os.makedirs(blobs_dir)

            # Create model file with full sha256 name
            full_name = "sha256-abc123def456"
            model_file = os.path.join(blobs_dir, full_name)
            with open(model_file, 'w') as f:
                f.write("model")

            # Search with partial identifier
            result = model_paths.resolve_model_path(
                "abc123",
                additional_paths=[ollama_dir]
            )

            self.assertEqual(result, os.path.abspath(model_file))


class TestListAvailableModels(unittest.TestCase):
    """Test list_available_models function."""

    def test_empty_search_paths(self):
        """Should return empty dict if no models found."""
        with patch('os.path.isdir', return_value=False):
            result = model_paths.list_available_models()
            self.assertIsInstance(result, dict)

    def test_finds_gguf_models(self):
        """Should find GGUF models in search paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test model files
            model1 = os.path.join(tmpdir, "model1.gguf")
            model2 = os.path.join(tmpdir, "model2.gguf")

            with open(model1, 'w') as f:
                f.write("test1")
            with open(model2, 'w') as f:
                f.write("test2")

            # Patch the search paths to only search our temp dir
            with patch.object(model_paths, 'DEFAULT_MODEL_SEARCH_PATHS', [tmpdir]):
                result = model_paths.list_available_models()

                self.assertIn(tmpdir, result)
                self.assertEqual(len(result[tmpdir]), 2)

    def test_filters_by_extension(self):
        """Should filter models by extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with different extensions
            gguf_file = os.path.join(tmpdir, "model.gguf")
            txt_file = os.path.join(tmpdir, "readme.txt")

            with open(gguf_file, 'w') as f:
                f.write("model")
            with open(txt_file, 'w') as f:
                f.write("readme")

            with patch.object(model_paths, 'DEFAULT_MODEL_SEARCH_PATHS', [tmpdir]):
                result = model_paths.list_available_models()

                # Should only find .gguf file
                self.assertEqual(len(result[tmpdir]), 1)
                self.assertEqual(result[tmpdir][0]['filename'], 'model.gguf')

    def test_custom_extensions(self):
        """Should use custom extensions when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_file = os.path.join(tmpdir, "model.custom")

            with open(custom_file, 'w') as f:
                f.write("model")

            with patch.object(model_paths, 'DEFAULT_MODEL_SEARCH_PATHS', [tmpdir]):
                result = model_paths.list_available_models(search_extensions=['.custom'])

                self.assertEqual(len(result[tmpdir]), 1)
                self.assertEqual(result[tmpdir][0]['filename'], 'model.custom')

    def test_includes_file_metadata(self):
        """Should include file metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = os.path.join(tmpdir, "model.gguf")

            with open(model_file, 'w') as f:
                f.write("x" * 1024)  # 1KB

            with patch.object(model_paths, 'DEFAULT_MODEL_SEARCH_PATHS', [tmpdir]):
                result = model_paths.list_available_models()

                model_info = result[tmpdir][0]
                self.assertIn('filename', model_info)
                self.assertIn('relative_path', model_info)
                self.assertIn('full_path', model_info)
                self.assertIn('size_mb', model_info)
                self.assertGreater(model_info['size_mb'], 0)

    def test_walks_subdirectories(self):
        """Should find models in subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)

            model_file = os.path.join(subdir, "model.gguf")
            with open(model_file, 'w') as f:
                f.write("test")

            with patch.object(model_paths, 'DEFAULT_MODEL_SEARCH_PATHS', [tmpdir]):
                result = model_paths.list_available_models()

                self.assertEqual(len(result[tmpdir]), 1)
                self.assertIn('subdir', result[tmpdir][0]['relative_path'])


class TestSetupModelsDirectory(unittest.TestCase):
    """Test setup_models_directory function."""

    def test_creates_directory(self):
        """Should create models directory if it doesn't exist."""
        with patch.object(model_paths, 'get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)

                result = model_paths.setup_models_directory()

                self.assertTrue(result.exists())
                self.assertTrue(result.is_dir())
                self.assertEqual(result.name, "models")

    def test_returns_existing_directory(self):
        """Should return existing directory without error."""
        with patch.object(model_paths, 'get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)

                # Create directory first
                models_dir = Path(tmpdir) / "models"
                models_dir.mkdir()

                # Call again
                result = model_paths.setup_models_directory()

                self.assertTrue(result.exists())
                self.assertEqual(result, models_dir)


class TestCreateModelSymlink(unittest.TestCase):
    """Test create_model_symlink function."""

    def test_creates_symlink(self):
        """Should create symlink to target file."""
        with patch.object(model_paths, 'get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)

                # Create target file
                target_file = os.path.join(tmpdir, "target.gguf")
                with open(target_file, 'w') as f:
                    f.write("model")

                result = model_paths.create_model_symlink(target_file, "link.gguf")

                self.assertIsNotNone(result)
                self.assertTrue(result.is_symlink())
                self.assertEqual(result.name, "link.gguf")

    def test_target_not_exists(self):
        """Should return None if target doesn't exist."""
        with patch.object(model_paths, 'get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)

                result = model_paths.create_model_symlink("/nonexistent/file.gguf", "link.gguf")

                self.assertIsNone(result)

    def test_replaces_existing_symlink(self):
        """Should replace existing symlink."""
        with patch.object(model_paths, 'get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)

                # Create two target files
                target1 = os.path.join(tmpdir, "target1.gguf")
                target2 = os.path.join(tmpdir, "target2.gguf")

                with open(target1, 'w') as f:
                    f.write("model1")
                with open(target2, 'w') as f:
                    f.write("model2")

                # Create first symlink
                link1 = model_paths.create_model_symlink(target1, "link.gguf")
                self.assertIsNotNone(link1)

                # Replace with new symlink
                link2 = model_paths.create_model_symlink(target2, "link.gguf")
                self.assertIsNotNone(link2)

                # Should point to target2 now
                self.assertTrue(link2.resolve().samefile(target2))

    def test_does_not_overwrite_regular_file(self):
        """Should not overwrite regular files."""
        with patch.object(model_paths, 'get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)

                # Create models directory
                models_dir = Path(tmpdir) / "models"
                models_dir.mkdir()

                # Create a regular file
                regular_file = models_dir / "existing.gguf"
                with open(regular_file, 'w') as f:
                    f.write("existing")

                # Create target
                target = os.path.join(tmpdir, "target.gguf")
                with open(target, 'w') as f:
                    f.write("target")

                result = model_paths.create_model_symlink(target, "existing.gguf")

                self.assertIsNone(result)
                # Original file should still exist
                self.assertTrue(regular_file.exists())
                self.assertFalse(regular_file.is_symlink())

    @patch('pathlib.Path.symlink_to')
    def test_handles_symlink_error(self, mock_symlink):
        """Should handle symlink creation errors."""
        mock_symlink.side_effect = OSError("Permission denied")

        with patch.object(model_paths, 'get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)

                target = os.path.join(tmpdir, "target.gguf")
                with open(target, 'w') as f:
                    f.write("model")

                result = model_paths.create_model_symlink(target, "link.gguf")

                self.assertIsNone(result)


def run_tests():
    """Run all model paths tests."""
    print("=" * 80)
    print("Testing Model Paths")
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
