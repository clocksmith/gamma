"""Build the declared apps offline and exercise their installed exports outside the checkout."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import venv
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(importlib.util.find_spec("setuptools") and importlib.util.find_spec("wheel"), "wheel verification needs installed setuptools and wheel")
class InstalledApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="gamma-app-installed-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        cls.outside = cls.directory / "outside-checkout"
        cls.outside.mkdir()
        cls.wheels = cls.directory / "wheels"
        cls.wheels.mkdir()
        cls.environment = {**os.environ, "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONNOUSERSITE": "1"}
        cls.environment.pop("PYTHONPATH", None)
        cls.environment.pop("GAMMA_CORE_SRC_PATH", None)
        cls.run_command([sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "--no-index", "--wheel-dir", str(cls.wheels),
                         str(ROOT / "gamma-core"), str(ROOT), str(ROOT / "apps/flux"), str(ROOT / "apps/mcp-server")], ROOT)
        cls.installation = cls.directory / "environment"
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(cls.installation)
        cls.bin = cls.installation / ("Scripts" if os.name == "nt" else "bin")
        cls.python = cls.bin / ("python.exe" if os.name == "nt" else "python")
        cls.run_command([str(cls.python), "-m", "pip", "install", "--no-deps", "--no-index", *map(str, cls.wheels.glob("*.whl"))])

    @classmethod
    def run_command(cls, command, cwd=None):
        result = subprocess.run(command, cwd=cwd or cls.outside, env=cls.environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        if result.returncode:
            raise AssertionError(f"{command[:4]} exited {result.returncode}\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
        return result

    def command(self, name):
        return str(self.bin / (name + ".exe" if os.name == "nt" else name))

    def test_wheels_contain_their_declared_entry_modules_and_resources(self):
        for pattern, required in [("flux_diffusion-*", ["flux.py", "src/core/gamma_core_path.py"]),
                                  ("gamma_mcp_server-*", ["gamma_mcp_server.py"])]:
            with ZipFile(next(self.wheels.glob(pattern))) as wheel:
                self.assertTrue(set(required).issubset(wheel.namelist()))
                self.assertFalse(any(name.startswith(("experiments/", "projects/", "games/")) for name in wheel.namelist()))
        self.assertEqual((self.installation / "share/flux/web/index.html").read_bytes(), (ROOT / "apps/flux/web/index.html").read_bytes())
        example = json.loads((self.installation / "share/gamma-mcp-server/claude_desktop_config.example.json").read_text())
        self.assertEqual(example["mcpServers"]["gamma"]["command"], "gamma-mcp-server")

    def test_flux_help_uses_installed_app_and_core_without_a_source_checkout(self):
        result = self.run_command([self.command("flux"), "--help"])
        self.assertIn("reconstruction", result.stdout)
        probe = self.run_command([str(self.python), "-c", """
import json, sys, flux, engine, gamma
from pathlib import Path
from src.core.gamma_core_path import configure_gamma_core_path
assert configure_gamma_core_path() is None
for module in [flux, engine, gamma]:
    assert Path(module.__file__).is_relative_to(Path(sys.prefix)), module.__file__
print(json.dumps({'installedCore': True, 'sourceOverride': False}))
"""])
        self.assertEqual(json.loads(probe.stdout), {"installedCore": True, "sourceOverride": False})

    @unittest.skipUnless(importlib.util.find_spec("mcp"), "actual MCP protocol verification needs the declared installed MCP SDK")
    def test_installed_mcp_help_and_real_stdio_tool_listing(self):
        self.assertIn("Gamma MCP server", self.run_command([self.command("gamma-mcp-server"), "--help"]).stdout)
        result = self.run_command([str(self.python), "-c", """
import asyncio, json, sys
from pathlib import Path
import gamma_mcp_server
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
assert Path(gamma_mcp_server.__file__).is_relative_to(Path(sys.prefix))
async def verify():
    server = StdioServerParameters(command=sys.argv[1], args=[])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            listed = await client.list_tools()
            print(json.dumps(sorted(tool.name for tool in listed.tools)))
asyncio.run(verify())
""", self.command("gamma-mcp-server")])
        self.assertEqual(json.loads(result.stdout), ["benchmark_model", "compare_models", "run_inference", "select_optimal_model"])


if __name__ == "__main__":
    unittest.main()
