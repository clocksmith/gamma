"""Doppler benchmark runner - wraps doppler CLI for WebGPU inference."""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from .base import BaseRunner, BenchResult


class DopplerRunner(BaseRunner):
    """Runner for Doppler WebGPU inference engine."""

    engine_name = "Doppler"

    # Default doppler path (relative to gamma: ../doppler)
    DEFAULT_DOPPLER_PATH = Path(__file__).parent.parent.parent.parent / "doppler"

    # Model aliases to doppler model names
    # Only include models that actually exist in doppler/models/
    MODEL_MAP = {
        "gemma-2-2b": "gemma-2-2b-it",
        "gemma-2-2b-it": "gemma-2-2b-it",
        "gemma2-2b": "gemma-2-2b-it",
    }

    def __init__(
        self,
        model_name: str,
        doppler_path: str | Path | None = None,
        kernel_profile: str = "fast",
        headed: bool = False,
        verbose: bool = True,
    ):
        super().__init__(model_name, "webgpu", verbose)
        self.doppler_path = Path(doppler_path) if doppler_path else self.DEFAULT_DOPPLER_PATH
        self.kernel_profile = kernel_profile
        self.headed = headed
        self._result_data: dict | None = None

        # Resolve model name
        self._doppler_model = self.MODEL_MAP.get(model_name.lower(), model_name)

    def get_model_info(self) -> dict:
        """Get model info."""
        info = {
            "quantization": "Q4 (WebGPU)",
            "size_gb": None,
            "backend": "WebGPU/Doppler",
            "kernel_profile": self.kernel_profile,
        }

        # Try to get more info from result if available
        if self._result_data and "model" in self._result_data:
            model_info = self._result_data["model"]
            if "quantization" in model_info:
                info["quantization"] = model_info["quantization"]

        return info

    def _check_doppler(self) -> bool:
        """Check if doppler is available."""
        cli_path = self.doppler_path / "cli" / "index.ts"
        return cli_path.exists()

    def load(self) -> None:
        """Verify doppler is available (actual loading happens in generate)."""
        if not self._check_doppler():
            raise RuntimeError(
                f"Doppler not found at {self.doppler_path}. "
                "Set doppler_path or ensure doppler exists."
            )

        # Check if npm dependencies are installed
        node_modules = self.doppler_path / "node_modules"
        if not node_modules.exists():
            self.log("Installing doppler dependencies...")
            result = subprocess.run(
                ["npm", "install"],
                cwd=self.doppler_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(f"npm install failed: {result.stderr}")

        self.log(f"Doppler ready at {self.doppler_path}")
        self.log(f"Model: {self._doppler_model}")
        self.log(f"Kernel profile: {self.kernel_profile}")

    def unload(self) -> None:
        """Nothing to unload - doppler CLI handles cleanup."""
        pass

    def generate(self, prompt: str, max_tokens: int) -> dict:
        """Run doppler benchmark and return metrics dict."""
        # Create temp file for output
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            # Build command
            cmd = [
                "npx", "tsx", "cli/index.ts", "bench",
                "--model", self._doppler_model,
                "--max-tokens", str(max_tokens),
                "--runs", "1",  # Single run per iteration
                "--output", output_path,
                "--kernel-profile", self.kernel_profile,
            ]

            if not self.headed:
                # Headless is default, but be explicit
                pass
            else:
                cmd.append("--headed")

            if not self.verbose:
                cmd.append("--quiet")

            # Run doppler CLI
            self.log(f"Running: {' '.join(cmd[:6])}...", end=" ", flush=True)

            result = subprocess.run(
                cmd,
                cwd=self.doppler_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise RuntimeError(f"Doppler bench failed: {error_msg[:200]}")

            # Parse output JSON
            with open(output_path, "r") as f:
                data = json.load(f)

            self._result_data = data

            # Extract metrics
            metrics = data.get("metrics", {})

            # Doppler reports detailed timing
            decode_tokens = metrics.get("decode_tokens", max_tokens)
            decode_time_ms = metrics.get("decode_ms_total", 0)
            decode_time_sec = decode_time_ms / 1000 if decode_time_ms > 0 else 1

            prefill_tokens = metrics.get("prefill_tokens", 0)
            prefill_time_ms = metrics.get("prefill_ms_total", 0)
            prefill_time_sec = prefill_time_ms / 1000 if prefill_time_ms > 0 else None

            ttft_ms = metrics.get("ttft_ms", 0)
            ttft_sec = ttft_ms / 1000 if ttft_ms > 0 else None

            # Get generated text from raw.generated_text
            raw = data.get("raw", {})
            generated_text = raw.get("generated_text", "")

            output = {
                "decode_tokens": decode_tokens,
                "decode_time_sec": decode_time_sec,
                "text": generated_text,
            }

            if prefill_tokens > 0:
                output["prefill_tokens"] = prefill_tokens
            if prefill_time_sec is not None:
                output["prefill_time_sec"] = prefill_time_sec
            if ttft_sec is not None:
                output["ttft_sec"] = ttft_sec

            return output

        finally:
            # Cleanup temp file
            try:
                os.unlink(output_path)
            except OSError:
                pass

    def run(
        self,
        prompt: str,
        max_tokens: int = 100,
        iterations: int = 3,
        warmup: bool = True,
    ) -> BenchResult:
        """Run doppler benchmark with proper warmup.

        Note: Doppler handles warmup internally, so we run the full benchmark
        once and extract the aggregated metrics.
        """
        self.log(f"\n{'='*60}")
        self.log(f"Benchmarking {self.engine_name}: {self.model_name}")
        self.log(f"{'='*60}")

        info = self.get_model_info()
        self.log(f"Quantization: {info.get('quantization', 'unknown')}")
        self.log(f"Kernel Profile: {self.kernel_profile}")

        # Load/verify
        try:
            self.load()
        except Exception as e:
            return BenchResult(
                name=self.model_name,
                engine=self.engine_name,
                tokens_per_sec=0,
                total_tokens=0,
                elapsed_sec=0,
                quantization=info.get("quantization", "unknown"),
                error=str(e),
            )

        # Run doppler with multiple runs (it handles aggregation)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            cmd = [
                "npx", "tsx", "cli/index.ts", "bench",
                "--model", self._doppler_model,
                "--max-tokens", str(max_tokens),
                "--runs", str(iterations),
                "--warmup", "1" if warmup else "0",
                "--output", output_path,
                "--kernel-profile", self.kernel_profile,
            ]

            if self.headed:
                cmd.append("--headed")

            self.log(f"Running {iterations} iterations with {'warmup' if warmup else 'no warmup'}...")

            result = subprocess.run(
                cmd,
                cwd=self.doppler_path,
                capture_output=True,
                text=True,
                timeout=600,  # 10 min timeout for multiple runs
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return BenchResult(
                    name=self.model_name,
                    engine=self.engine_name,
                    tokens_per_sec=0,
                    total_tokens=0,
                    elapsed_sec=0,
                    quantization=info.get("quantization", "unknown"),
                    error=f"Doppler failed: {error_msg[:200]}",
                )

            # Parse output JSON
            with open(output_path, "r") as f:
                data = json.load(f)

            self._result_data = data
            metrics = data.get("metrics", {})

            # Extract key metrics
            decode_tps = metrics.get("decode_tokens_per_sec", 0)
            prefill_tps = metrics.get("prefill_tokens_per_sec", 0)
            decode_tokens = metrics.get("decode_tokens", 0)
            prefill_tokens = metrics.get("prefill_tokens", 0)
            decode_ms = metrics.get("decode_ms_total", 0)
            prefill_ms = metrics.get("prefill_ms_total", 0)
            ttft_ms = metrics.get("ttft_ms", 0)
            vram_bytes = metrics.get("estimated_vram_bytes_peak", 0)

            # Report results
            self.log(f"\nResults:")
            self.log(f"  TTFT:    {ttft_ms:.1f} ms")
            self.log(f"  Prefill: {prefill_tps:.2f} tok/s")
            self.log(f"  Decode:  {decode_tps:.2f} tok/s")
            if vram_bytes:
                self.log(f"  VRAM:    {vram_bytes / 1024 / 1024:.1f} MB")

            # Update info with actual data
            info = self.get_model_info()
            vram_gb = None
            if vram_bytes:
                vram_gb = vram_bytes / 1024 / 1024 / 1024

            # Get generated text from raw.generated_text
            raw = data.get("raw", {})
            sample_output = raw.get("generated_text", "")

            return BenchResult(
                name=self.model_name,
                engine=self.engine_name,
                tokens_per_sec=decode_tps,  # Use decode speed as primary metric
                total_tokens=decode_tokens * iterations,
                elapsed_sec=decode_ms / 1000 if decode_ms else 0,
                quantization=info.get("quantization", "Q4 (WebGPU)"),
                model_size_gb=info.get("size_gb"),
                vram_gb=vram_gb,
                iterations=iterations,
                per_iteration=[{
                    "prefill_tokens_per_sec": prefill_tps,
                    "decode_tokens_per_sec": decode_tps,
                    "ttft_ms": ttft_ms,
                }],
                sample_output=sample_output,
                # New granular metrics
                prefill_tokens_per_sec=prefill_tps if prefill_tps > 0 else None,
                decode_tokens_per_sec=decode_tps if decode_tps > 0 else None,
                ttft_ms=ttft_ms if ttft_ms > 0 else None,
                prefill_tokens=prefill_tokens * iterations if prefill_tokens > 0 else None,
                decode_tokens=decode_tokens * iterations if decode_tokens > 0 else None,
            )

        finally:
            try:
                os.unlink(output_path)
            except OSError:
                pass
