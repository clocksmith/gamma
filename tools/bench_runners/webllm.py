"""WebLLM benchmark runner using Playwright with WebGPU."""

import json
import tempfile
import time
from pathlib import Path

from .base import BaseRunner


# HTML template for WebLLM benchmark
WEBLLM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>WebLLM Benchmark</title>
    <script type="module">
        import * as webllm from "https://esm.run/@mlc-ai/web-llm";

        window.benchmarkState = {
            ready: false,
            running: false,
            result: null,
            error: null,
            progress: ""
        };

        window.initModel = async (modelId) => {
            try {
                window.benchmarkState.progress = "Initializing...";

                const engine = await webllm.CreateMLCEngine(modelId, {
                    initProgressCallback: (progress) => {
                        window.benchmarkState.progress = progress.text;
                        console.log("Init progress:", progress.text);
                    }
                });

                window.engine = engine;
                window.benchmarkState.ready = true;
                window.benchmarkState.progress = "Ready";
                return true;
            } catch (e) {
                window.benchmarkState.error = e.toString();
                return false;
            }
        };

        window.runBenchmark = async (prompt, maxTokens) => {
            if (!window.engine) {
                window.benchmarkState.error = "Engine not initialized";
                return null;
            }

            window.benchmarkState.running = true;

            try {
                const startTime = performance.now();

                const response = await window.engine.chat.completions.create({
                    messages: [{ role: "user", content: prompt }],
                    max_tokens: maxTokens,
                    temperature: 0,
                    stream: false
                });

                const endTime = performance.now();
                const elapsedSec = (endTime - startTime) / 1000;

                // Get token count from usage
                const outputTokens = response.usage?.completion_tokens || 0;

                window.benchmarkState.result = {
                    tokens: outputTokens,
                    elapsed: elapsedSec,
                    tokensPerSec: outputTokens / elapsedSec,
                    text: response.choices[0]?.message?.content || ""
                };

                window.benchmarkState.running = false;
                return window.benchmarkState.result;
            } catch (e) {
                window.benchmarkState.error = e.toString();
                window.benchmarkState.running = false;
                return null;
            }
        };

        window.getModelInfo = async () => {
            if (!window.engine) return null;
            try {
                // WebLLM models are typically quantized
                return {
                    quantization: "INT4 (WebGPU)",
                    backend: "WebGPU"
                };
            } catch (e) {
                return null;
            }
        };

        window.cleanup = async () => {
            if (window.engine) {
                try {
                    await window.engine.unload();
                } catch (e) {}
                window.engine = null;
            }
            window.benchmarkState.ready = false;
        };
    </script>
</head>
<body>
    <h1>WebLLM Benchmark</h1>
    <div id="status">Loading...</div>
</body>
</html>
"""


class WebLLMRunner(BaseRunner):
    """Runner for WebLLM models using Playwright with WebGPU."""

    engine_name = "WebLLM"

    # WebLLM model mapping (common names to WebLLM model IDs)
    MODEL_MAP = {
        "llama-3-8b": "Llama-3-8B-Instruct-q4f16_1-MLC",
        "llama-3.1-8b": "Llama-3.1-8B-Instruct-q4f16_1-MLC",
        "llama-3.2-1b": "Llama-3.2-1B-Instruct-q4f16_1-MLC",
        "llama-3.2-3b": "Llama-3.2-3B-Instruct-q4f16_1-MLC",
        "gemma-2-2b": "gemma-2-2b-it-q4f16_1-MLC",
        "gemma-2-9b": "gemma-2-9b-it-q4f16_1-MLC",
        "phi-3.5-mini": "Phi-3.5-mini-instruct-q4f16_1-MLC",
        "qwen2-1.5b": "Qwen2-1.5B-Instruct-q4f16_1-MLC",
        "qwen2-7b": "Qwen2-7B-Instruct-q4f16_1-MLC",
        "mistral-7b": "Mistral-7B-Instruct-v0.3-q4f16_1-MLC",
        "smollm-1.7b": "SmolLM-1.7B-Instruct-q4f16_1-MLC",
    }

    def __init__(
        self,
        model_name: str,
        headless: bool = True,
        verbose: bool = True,
    ):
        super().__init__(model_name, "webgpu", verbose)
        self.headless = headless
        self._browser = None
        self._page = None
        self._temp_dir = None

        # Resolve model name
        self._webllm_model = self.MODEL_MAP.get(model_name.lower(), model_name)

    def get_model_info(self) -> dict:
        """Get model info."""
        return {
            "quantization": "INT4 (WebGPU)",
            "size_gb": None,
            "backend": "WebGPU",
        }

    def _get_browser_args(self) -> list[str]:
        """Get Chromium args for WebGPU with real GPU."""
        return [
            "--enable-unsafe-webgpu",
            "--enable-features=Vulkan,UseSkiaRenderer",
            "--use-vulkan",
            "--enable-gpu-rasterization",
            "--enable-zero-copy",
            "--ignore-gpu-blocklist",
            "--disable-gpu-sandbox",
            "--use-angle=vulkan",
            "--enable-webgpu-developer-features",
            # Storage/cache fixes
            "--disable-web-security",
            "--allow-file-access-from-files",
        ]

    def load(self) -> None:
        """Launch browser and load WebLLM."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("Playwright not installed. Install with: pip install playwright && playwright install chromium")

        self.log("Launching browser with WebGPU...")

        # Create temp dir for HTML and browser data
        self._temp_dir = tempfile.mkdtemp()
        html_path = Path(self._temp_dir) / "benchmark.html"
        html_path.write_text(WEBLLM_HTML)

        # Create persistent user data dir for cache/storage
        user_data_dir = Path(self._temp_dir) / "browser_data"
        user_data_dir.mkdir(exist_ok=True)

        # Launch browser with persistent context for cache support
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=self.headless,
            args=self._get_browser_args(),
        )

        self._page = self._context.new_page()
        self._page.goto(f"file://{html_path}")

        # Wait for page to load
        self._page.wait_for_function("typeof window.initModel === 'function'", timeout=30000)

        # Initialize model
        self.log(f"Loading WebLLM model: {self._webllm_model}")
        self._page.evaluate(f"window.initModel('{self._webllm_model}')")

        # Wait for model to be ready (with progress updates)
        max_wait = 300  # 5 minutes for model download
        start = time.time()
        while time.time() - start < max_wait:
            state = self._page.evaluate("window.benchmarkState")
            if state.get("ready"):
                self.log("Model loaded")
                return
            if state.get("error"):
                raise RuntimeError(f"WebLLM error: {state['error']}")

            progress = state.get("progress", "")
            if progress and self.verbose:
                print(f"\r  {progress[:60]:<60}", end="", flush=True)

            time.sleep(0.5)

        raise RuntimeError("Timeout waiting for WebLLM model to load")

    def unload(self) -> None:
        """Close browser and cleanup."""
        if self._page:
            try:
                self._page.evaluate("window.cleanup()")
            except Exception:
                pass
            self._page = None

        if hasattr(self, '_context') and self._context:
            self._context.close()
            self._context = None

        if hasattr(self, '_browser') and self._browser:
            self._browser.close()
            self._browser = None

        if self._playwright:
            self._playwright.stop()
            self._playwright = None

        # Cleanup temp dir
        if self._temp_dir:
            import shutil
            try:
                shutil.rmtree(self._temp_dir)
            except Exception:
                pass
            self._temp_dir = None

    def generate(self, prompt: str, max_tokens: int) -> tuple[int, float]:
        """Generate tokens using WebLLM."""
        if not self._page:
            raise RuntimeError("Browser not initialized")

        # Run benchmark
        result = self._page.evaluate(
            f"window.runBenchmark({json.dumps(prompt)}, {max_tokens})"
        )

        if result is None:
            state = self._page.evaluate("window.benchmarkState")
            raise RuntimeError(f"WebLLM generation failed: {state.get('error', 'unknown')}")

        return result["tokens"], result["elapsed"]
