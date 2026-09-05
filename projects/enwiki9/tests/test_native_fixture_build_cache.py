"""Synthetic compile-only cache regression tests; no corpus or gate launches."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from lib import native_fixture_build_cache as cache


@unittest.skipUnless(shutil.which("g++") and shutil.which("prlimit"), "requires existing g++ and prlimit")
class NativeFixtureBuildCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="native cache fixture ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cache_dir = self.root / "cache with spaces"
        self.header = self.root / "value #$ header.hpp"
        self.bridge = self.root / "included implementation.cpp"
        self.source = self.root / "main source.cpp"
        self.header.write_text("#pragma once\n#include <cstdint>\nconstexpr std::uint32_t value = 7;\n")
        self.bridge.write_text(f'#include "{self.header.name}"\nint answer() {{ return value; }}\n')
        self.source.write_text(f'#include "{self.bridge.name}"\nint main() {{ return answer(); }}\n')
        self.flags = ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror"]

    def build(self, **overrides):
        arguments = dict(sources=[self.source], flags=self.flags, cache_dir=self.cache_dir, timeout_seconds=60)
        arguments.update(overrides)
        return cache.build_cpp_cached(**arguments)

    def execute(self, result):
        return subprocess.run([str(result.binary)], timeout=5, check=False).returncode

    def test_first_build_verified_hit_and_transitive_cpp_system_dependencies(self):
        first = self.build()
        self.assertFalse(first.cache_hit)
        self.assertEqual(first.cache_reason, "absent")
        self.assertEqual(self.execute(first), 7)
        second = self.build()
        self.assertTrue(second.cache_hit)
        self.assertEqual(second.cache_reason, "verified")
        self.assertEqual(first.binary, second.binary)
        self.assertEqual(first.manifest, second.manifest)
        dependencies = first.manifest["identity"]["dependencies"]
        paths = {item["path"] for item in dependencies}
        self.assertTrue({str(self.source), str(self.header), str(self.bridge)} <= paths)
        self.assertTrue(any("/include/" in path for path in paths))
        self.assertTrue(all(len(item["sha256"]) == 64 and item["bytes"] > 0 for item in dependencies))

    def test_header_source_and_flags_each_invalidate_without_deleting_previous_entries(self):
        first = self.build()
        self.header.write_text("#pragma once\nconstexpr unsigned value = 9;\n")
        header = self.build()
        self.assertFalse(header.cache_hit)
        self.assertEqual(self.execute(header), 9)
        self.source.write_text(f'#include "{self.bridge.name}"\nint main() {{ return answer() + 2; }}\n')
        source = self.build()
        self.assertFalse(source.cache_hit)
        self.assertEqual(self.execute(source), 11)
        flags = self.build(flags=[*self.flags, "-DUNUSED_FIXTURE_FLAG=1"])
        self.assertFalse(flags.cache_hit)
        self.assertEqual(self.execute(flags), 11)
        self.assertEqual(len({result.binary for result in (first, header, source, flags)}), 4)
        self.assertTrue(all(result.binary.exists() for result in (first, header, source, flags)))

    def test_changed_include_resolution_cannot_reuse_old_dependencies(self):
        include_a = self.root / "a"
        include_b = self.root / "b"
        include_a.mkdir()
        include_b.mkdir()
        (include_b / "selected.hpp").write_text("constexpr int selected = 3;\n")
        self.source.write_text("#include <selected.hpp>\nint main() { return selected; }\n")
        flags = [*self.flags, "-I", str(include_a), "-I", str(include_b)]
        first = self.build(flags=flags)
        (include_a / "selected.hpp").write_text("constexpr int selected = 4;\n")
        second = self.build(flags=flags)
        self.assertFalse(second.cache_hit)
        self.assertNotEqual(first.binary, second.binary)
        self.assertEqual(self.execute(second), 4)

    def test_binary_corruption_is_quarantined_and_rebuilt(self):
        first = self.build()
        first.binary.chmod(0o700)
        first.binary.write_bytes(b"corrupted derived binary")
        second = self.build()
        self.assertFalse(second.cache_hit)
        self.assertEqual(second.cache_reason, "binary_digest_mismatch")
        self.assertEqual(self.execute(second), 7)
        quarantined = list((self.cache_dir / "quarantine").glob("*/program"))
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0].read_bytes(), b"corrupted derived binary")

    def test_corrupt_manifest_and_falsified_identity_fail_closed(self):
        first = self.build()
        manifest_path = first.binary.parent / "manifest.json"
        manifest_path.write_text("{not valid json\n")
        second = self.build()
        self.assertFalse(second.cache_hit)
        self.assertEqual(second.cache_reason, "invalid_manifest_or_binary")
        value = json.loads(manifest_path.read_text())
        value["identity"]["dependencies"][0]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(value))
        third = self.build()
        self.assertFalse(third.cache_hit)
        self.assertEqual(third.cache_reason, "manifest_identity_mismatch")
        self.assertEqual(self.execute(third), 7)

    def test_concurrent_requests_publish_once_and_reuse_exact_binary(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.build) for _ in range(2)]
            results = [future.result(timeout=60) for future in futures]
        self.assertEqual(sorted(result.cache_hit for result in results), [False, True])
        self.assertEqual(results[0].binary, results[1].binary)
        self.assertEqual(results[0].manifest, results[1].manifest)
        self.assertEqual(len(list((self.cache_dir / "entries").iterdir())), 1)

    def test_ambient_compiler_injection_is_not_inherited(self):
        with mock.patch.dict(os.environ, {"CPATH": "/not/a/real/include", "CXXFLAGS": "--bad-flag",
                                          "LD_PRELOAD": "/not/a/real/library.so"}):
            result = self.build()
        self.assertEqual(self.execute(result), 7)
        self.assertEqual(result.manifest["identity"]["environment"], cache.BUILD_ENVIRONMENT)
        self.assertNotIn("LD_PRELOAD", result.manifest["identity"]["environment"])

    def test_changed_compiler_wrapper_changes_identity(self):
        wrapper = self.root / "compiler wrapper"
        real_compiler = shutil.which("g++")
        wrapper.write_text(f'#!/bin/sh\nexec "{real_compiler}" "$@"\n')
        wrapper.chmod(0o700)
        first = self.build(compiler=str(wrapper))
        wrapper.write_text(f'#!/bin/sh\n# changed driver identity\nexec "{real_compiler}" "$@"\n')
        second = self.build(compiler=str(wrapper))
        self.assertFalse(second.cache_hit)
        self.assertNotEqual(first.binary, second.binary)

    def test_source_change_during_build_is_not_published(self):
        original_run = cache._run

        def mutate_after_build(command, **kwargs):
            result = original_run(command, **kwargs)
            if "-o" in command:
                self.header.write_text("constexpr unsigned value = 19;\n")
            return result

        with mock.patch.object(cache, "_run", side_effect=mutate_after_build):
            with self.assertRaisesRegex(cache.BuildCacheError, "changed during build"):
                self.build()
        self.assertEqual(list((self.cache_dir / "entries").iterdir()), [])

    def test_source_change_during_cache_hit_verification_is_rejected(self):
        self.build()
        original_cached = cache._cached

        def mutate_after_cached(*args):
            result = original_cached(*args)
            self.header.write_text("constexpr unsigned value = 23;\n")
            return result

        with mock.patch.object(cache, "_cached", side_effect=mutate_after_cached):
            with self.assertRaisesRegex(cache.BuildCacheError, "changed during cache verification"):
                self.build()

    def test_tampered_bounds_and_binary_symlink_are_not_reused(self):
        first = self.build()
        manifest_path = first.binary.parent / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["bounds"]["address_space_bytes"] = cache.ADDRESS_SPACE_BYTES + 1
        manifest_path.write_text(json.dumps(manifest))
        second = self.build()
        self.assertFalse(second.cache_hit)
        self.assertEqual(second.cache_reason, "invalid_manifest_bounds")
        preserved = self.root / "preserved real binary"
        second.binary.rename(preserved)
        second.binary.symlink_to(preserved)
        third = self.build()
        self.assertFalse(third.cache_hit)
        self.assertEqual(third.cache_reason, "invalid_binary")
        self.assertTrue(preserved.exists())
        self.assertEqual(self.execute(third), 7)

    def test_backslash_in_dependency_path_is_not_silently_misparsed(self):
        for name in ("back\\slash.hpp", "back\\ slash.hpp", "back\\\\slash.hpp", "back\\#slash.hpp"):
            with self.subTest(name=name):
                header = self.root / name
                header.write_text("constexpr int answer = 5;\n")
                self.source.write_text(f'#include "{header.name}"\nint main() {{ return answer; }}\n')
                result = self.build()
                self.assertEqual(self.execute(result), 5)
                self.assertIn(str(header), {item["path"] for item in result.manifest["identity"]["dependencies"]})

    def test_stricter_inherited_hard_limits_are_preserved(self):
        code = """
import json
from pathlib import Path
import resource
import sys
sys.path.insert(0, sys.argv[1])
from lib.native_fixture_build_cache import build_cpp_cached
resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024, 32 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
result = build_cpp_cached(sources=[Path(sys.argv[2])], flags=['-std=c++20', '-O2'],
                          cache_dir=Path(sys.argv[3]), timeout_seconds=60)
print(json.dumps(result.manifest['bounds']))
"""
        result = subprocess.run([sys.executable, "-c", code, str(PROJECT), str(self.source), str(self.cache_dir)],
                                check=True, capture_output=True, text=True, timeout=60)
        bounds = json.loads(result.stdout)
        self.assertEqual(bounds["address_space_bytes"], 1024 * 1024 * 1024)
        self.assertEqual(bounds["per_file_bytes"], 32 * 1024 * 1024)
        self.assertEqual(bounds["cpu_seconds_per_process_ceiling"], 12)

    def test_deadline_terminates_owned_compiler_process(self):
        wrapper = self.root / "blocked compiler"
        wrapper.write_text("#!/bin/sh\nsleep 10\n")
        wrapper.chmod(0o700)
        with self.assertRaises(cache.BuildCacheTimeout):
            self.build(compiler=str(wrapper), timeout_seconds=1)
        self.assertEqual(list((self.cache_dir / "entries").iterdir()), [])

    def test_temporal_macros_and_unbound_inputs_are_rejected(self):
        self.source.write_text('const char* build_time = __TIME__;\nint main() { return build_time[0]; }\n')
        with self.assertRaisesRegex(cache.BuildCacheError, "date-time"):
            self.build()
        for flags in (["-o", "elsewhere"], ["@response"], ["-Wl,-rpath,/tmp"], ["-march=native"],
                      ["-fplugin=plugin.so"], ["-I"], ["-include", "-bad"], ["-save-temps"]):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                self.build(flags=flags)

    def test_implicit_precompiled_header_is_rejected(self):
        self.header.with_name(self.header.name + ".gch").write_bytes(b"not a supported bound input")
        with self.assertRaisesRegex(cache.BuildCacheError, "precompiled headers are unsupported"):
            self.build()


if __name__ == "__main__":
    unittest.main()
