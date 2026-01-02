"""Ollama benchmark runner."""

import subprocess

import requests

from .base import BaseRunner


class OllamaRunner(BaseRunner):
    """Runner for Ollama models."""

    engine_name = "Ollama"

    def __init__(
        self,
        model_name: str,
        host: str = "http://localhost:11434",
        device: str = "auto",
        verbose: bool = True,
    ):
        super().__init__(model_name, device, verbose)
        self.host = host.rstrip("/")
        self._model_info: dict | None = None

    def get_model_info(self) -> dict:
        """Get model info from Ollama."""
        if self._model_info:
            return self._model_info

        info = {"quantization": "unknown", "size_gb": None, "params": None}

        try:
            # Use 'ollama show' to get model details
            result = subprocess.run(
                ["ollama", "show", self.model_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            show_output = result.stdout

            for line in show_output.split("\n"):
                line_lower = line.lower()

                # Parse quantization
                if "quantization" in line_lower:
                    parts = line.split()
                    if len(parts) >= 2:
                        info["quantization"] = parts[-1].upper()

                # Parse parameters
                if "parameters" in line_lower:
                    parts = line.split()
                    if len(parts) >= 2:
                        info["params"] = parts[-1]

            # Fallback: check model name for quant hints
            if info["quantization"] == "unknown":
                name_lower = self.model_name.lower()
                quant_patterns = [
                    ("q4_0", "Q4_0"), ("q4_k_m", "Q4_K_M"), ("q4_k_s", "Q4_K_S"),
                    ("q4_k_l", "Q4_K_L"), ("q5_0", "Q5_0"), ("q5_k_m", "Q5_K_M"),
                    ("q5_k_s", "Q5_K_S"), ("q6_k", "Q6_K"), ("q8_0", "Q8_0"),
                    ("fp16", "FP16"), ("bf16", "BF16"), ("f32", "FP32"),
                    ("mxfp4", "MXFP4"), ("int4", "INT4"), ("int8", "INT8"),
                ]
                for pattern, label in quant_patterns:
                    if pattern in name_lower:
                        info["quantization"] = label
                        break

            # Get size from 'ollama list'
            # Format: "model_name    hash    13 GB     2 months ago"
            list_result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=10
            )
            for line in list_result.stdout.split("\n"):
                if self.model_name in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p == "GB" and i > 0:
                            # Format: "13 GB" - size is in previous part
                            try:
                                info["size_gb"] = float(parts[i - 1])
                            except (ValueError, IndexError):
                                pass
                            break
                        elif p == "MB" and i > 0:
                            try:
                                info["size_gb"] = float(parts[i - 1]) / 1024
                            except (ValueError, IndexError):
                                pass
                            break
                        elif p.endswith("GB"):
                            # Format: "13GB" - no space
                            try:
                                info["size_gb"] = float(p.replace("GB", ""))
                            except ValueError:
                                pass
                            break
                        elif p.endswith("MB"):
                            try:
                                info["size_gb"] = float(p.replace("MB", "")) / 1024
                            except ValueError:
                                pass
                            break
                    break

        except Exception as e:
            self.log(f"Warning: Could not get Ollama model info: {e}")

        self._model_info = info
        # Also set ram_gb for display
        if info["size_gb"]:
            info["ram_gb"] = info["size_gb"]
        return info

    def load(self) -> None:
        """Ensure model is loaded in Ollama (pull if needed)."""
        # Check if model exists
        try:
            response = requests.post(
                f"{self.host}/api/show",
                json={"name": self.model_name},
                timeout=10,
            )
            if response.status_code == 200:
                self.log("Model ready")
                return
        except requests.RequestException:
            pass

        # Try to pull if not found
        self.log(f"Model {self.model_name} not found, pulling...")
        try:
            response = requests.post(
                f"{self.host}/api/pull",
                json={"name": self.model_name, "stream": False},
                timeout=600,
            )
            if response.status_code == 200:
                self.log("Model pulled successfully")
            else:
                raise RuntimeError(f"Failed to pull model: {response.text}")
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to pull model: {e}")

    def unload(self) -> None:
        """Ollama manages its own memory, nothing to unload."""
        pass

    def generate(self, prompt: str, max_tokens: int) -> tuple[int, float, str]:
        """Generate tokens using Ollama API."""
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=120,
        )

        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.text}")

        data = response.json()

        eval_count = data.get("eval_count", 0)
        eval_duration_ns = data.get("eval_duration", 1)
        eval_duration_sec = eval_duration_ns / 1e9
        generated_text = data.get("response", "")

        return eval_count, eval_duration_sec, generated_text
