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
                const totalElapsedSec = (endTime - startTime) / 1000;

                // Get token counts from usage
                const usage = response.usage || {};
                const outputTokens = usage.completion_tokens || 0;
                const promptTokens = usage.prompt_tokens || 0;

                // Get detailed performance metrics from usage.extra if available
                // WebLLM provides prefill_tokens_per_s and decode_tokens_per_s
                const extra = usage.extra || {};
                const prefillTps = extra.prefill_tokens_per_s || null;
                const decodeTps = extra.decode_tokens_per_s || null;
                const ttftMs = extra.time_to_first_token_s ? extra.time_to_first_token_s * 1000 : null;

                // Calculate times from speeds if available
                let prefillTimeSec = null;
                let decodeTimeSec = null;
                if (prefillTps && promptTokens > 0) {
                    prefillTimeSec = promptTokens / prefillTps;
                }
                if (decodeTps && outputTokens > 0) {
                    decodeTimeSec = outputTokens / decodeTps;
                }

                window.benchmarkState.result = {
                    decodeTokens: outputTokens,
                    prefillTokens: promptTokens,
                    totalElapsedSec: totalElapsedSec,
                    decodeTimeSec: decodeTimeSec || totalElapsedSec,
                    prefillTimeSec: prefillTimeSec,
                    prefillTps: prefillTps,
                    decodeTps: decodeTps,
                    ttftMs: ttftMs,
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

    # Default cache directory
    DEFAULT_CACHE_DIR = Path.home() / ".cache" / "gamma" / "webllm"

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
        cache_dir: Path | str | None = None,
        clear_cache: bool = False,
    ):
        super().__init__(model_name, "webgpu", verbose)
        self.headless = headless
        self._browser = None
        self._page = None
        self._temp_dir = None

        # Resolve model name
        self._webllm_model = self.MODEL_MAP.get(model_name.lower(), model_name)

        # Setup cache directory (per-model to allow selective clearing)
        self._cache_dir = Path(cache_dir) if cache_dir else self.DEFAULT_CACHE_DIR
        self._model_cache_dir = self._cache_dir / self._webllm_model.replace("/", "_")

        # Clear cache if requested
        if clear_cache and self._model_cache_dir.exists():
            import shutil
            self.log(f"Clearing cache for {self._webllm_model}...")
            shutil.rmtree(self._model_cache_dir)

    def get_model_info(self) -> dict:
        """Get model info."""
        return {
            "quantization": "INT4 (WebGPU)",
            "size_gb": None,
            "backend": "WebGPU",
        }

    def _get_browser_args(self) -> list[str]:
        """Get Chromium args for WebGPU with real GPU."""
        import platform

        args = [
            "--enable-unsafe-webgpu",
            "--enable-gpu-rasterization",
            "--enable-zero-copy",
            "--ignore-gpu-blocklist",
            "--disable-gpu-sandbox",
            "--enable-webgpu-developer-features",
            # Enable shader-f16 for WebLLM models
            "--enable-dawn-features=allow_unsafe_apis,use_dxc",
            # Storage/cache fixes
            "--disable-web-security",
            "--allow-file-access-from-files",
        ]

        # Use Metal on macOS, Vulkan elsewhere
        if platform.system() == "Darwin":
            args.extend([
                "--use-angle=metal",
                "--enable-features=Vulkan,UseSkiaRenderer,SkiaGraphite",
            ])
        else:
            args.extend([
                "--use-angle=vulkan",
                "--use-vulkan",
                "--enable-features=Vulkan,UseSkiaRenderer",
            ])

        return args

    def load(self) -> None:
        """Launch browser and load WebLLM."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("Playwright not installed. Install with: pip install playwright && playwright install chromium")

        self.log("Launching browser with WebGPU...")

        # Create temp dir for HTML file only
        self._temp_dir = tempfile.mkdtemp()
        html_path = Path(self._temp_dir) / "benchmark.html"
        html_path.write_text(WEBLLM_HTML)

        # Use persistent cache dir for browser data (preserves IndexedDB model cache)
        self._model_cache_dir.mkdir(parents=True, exist_ok=True)
        user_data_dir = self._model_cache_dir / "browser_data"
        user_data_dir.mkdir(exist_ok=True)

        cache_status = "cached" if (user_data_dir / "Default" / "IndexedDB").exists() else "fresh"
        self.log(f"Cache dir: {self._model_cache_dir} ({cache_status})")

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
        """Close browser and cleanup (preserves model cache)."""
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

        # Only cleanup temp dir (HTML file), preserve cache dir
        if self._temp_dir:
            import shutil
            try:
                shutil.rmtree(self._temp_dir)
            except Exception:
                pass
            self._temp_dir = None

    def generate(self, prompt: str, max_tokens: int) -> dict:
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

        output = {
            "decode_tokens": result.get("decodeTokens", 0),
            "decode_time_sec": result.get("decodeTimeSec", result.get("totalElapsedSec", 0)),
            "text": result.get("text", ""),
        }

        # Add prefill metrics if available
        if result.get("prefillTokens"):
            output["prefill_tokens"] = result["prefillTokens"]
        if result.get("prefillTimeSec"):
            output["prefill_time_sec"] = result["prefillTimeSec"]
        if result.get("ttftMs"):
            output["ttft_sec"] = result["ttftMs"] / 1000  # Convert ms to sec

        return output
