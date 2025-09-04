"""
A shared utility module for the Jetson LLM Engine project.

This module centralizes common functions for system inspection, GPU verification,
and model loading to ensure consistency across all executable scripts.
"""

import argparse
import os
import platform
import sys
import threading
import time
import itertools
from typing import Optional

from llama_cpp import Llama, llama_supports_gpu_offload
import psutil

try:
    from pynvml import (
        nvmlInit,
        nvmlShutdown,
        nvmlDeviceGetCount,
        nvmlDeviceGetHandleByIndex,
        nvmlDeviceGetName,
        NVMLError,
    )

    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False


class Spinner:
    """A simple terminal spinner to indicate a process is running."""

    def __init__(self, message: str = "Loading...", delay: float = 0.1):
        """Initializes the spinner.

        Args:
            message: The message to display next to the spinner.
            delay: The speed of the spinner animation.
        """
        self.spinner = itertools.cycle(["-", "/", "|", "\\"])
        self.delay = delay
        self.busy = False
        self.thread = threading.Thread(target=self._spin)
        self.message = message

    def _spin(self) -> None:
        """Runs the spinner loop in a separate thread."""
        while self.busy:
            sys.stdout.write(f"\r{self.message} {next(self.spinner)}")
            sys.stdout.flush()
            time.sleep(self.delay)

    def start(self) -> None:
        """Starts the spinner."""
        self.busy = True
        self.thread.start()

    def stop(self) -> None:
        """Stops the spinner and cleans up the line."""
        self.busy = False
        self.thread.join()
        sys.stdout.write(f"\r{' ' * (len(self.message) + 2)}\r")
        sys.stdout.flush()


def add_common_cli_args(parser: argparse.ArgumentParser) -> None:
    """Adds common command-line arguments to a parser.

    Args:
        parser: The argparse.ArgumentParser instance to add arguments to.
    """
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        required=True,
        help="Filename of the GGUF model in the 'models/' directory.",
    )
    parser.add_argument(
        "--n-gpu-layers",
        type=int,
        default=-1,
        help="Number of layers to offload to GPU (-1 for all possible). Set to 0 for CPU-only.",
    )
    parser.add_argument(
        "--n-ctx",
        type=int,
        default=4096,
        help="Context window size for the model.",
    )


def verify_and_report_gpu_support() -> None:
    """Checks for and reports GPU offload capability."""
    print("--- Hardware Acceleration Status ---")
    if llama_supports_gpu_offload():
        print("\033[92m[✔] SUCCESS: llama-cpp-python reports GPU support is available.\033[0m")
        if NVML_AVAILABLE:
            try:
                nvmlInit()
                handle = nvmlDeviceGetHandleByIndex(0)
                gpu_name = nvmlDeviceGetName(handle)
                print(f"    GPU Detected: {gpu_name}")
                nvmlShutdown()
            except NVMLError:
                print("\033[93m    Warning: NVML found, but could not query GPU name.\033[0m")
        else:
            print("\033[93m    Warning: pynvml not found. Cannot display GPU name.\033[0m")
    else:
        print("\033[91m[✖] FAILURE: GPU offload NOT SUPPORTED by this build.\033[0m")
        print("\033[91m    Model will run on CPU only, resulting in very slow performance.\033[0m")
        print("\033[93m    To fix this, re-run './setup.sh' and check for any CUDA/nvcc build errors.\033[0m")
    print("------------------------------------\n")


def load_language_model(
    model_path: str, n_ctx: int, n_gpu_layers: int, is_chat: bool
) -> Optional[Llama]:
    """Loads the GGUF model with a spinner and error handling.

    Args:
        model_path: The full path to the .gguf model file.
        n_ctx: The context window size for the model.
        n_gpu_layers: The number of layers to offload to the GPU.
        is_chat: If True, loads the model with a chat format handler.

    Returns:
        An instance of the loaded Llama model, or None if loading fails.
    """
    spinner = Spinner(f"Loading model: {os.path.basename(model_path)}...")
    spinner.start()
    try:
        init_kwargs = {
            "model_path": model_path,
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
            "verbose": False,
        }
        if is_chat:
            init_kwargs["chat_format"] = "gemma"

        llm = Llama(**init_kwargs)
        spinner.stop()
        print("Model loaded successfully.")
        return llm
    except Exception as e:
        spinner.stop()
        print(f"\n\033[91mFatal error loading model: {e}\033[0m")
        return None