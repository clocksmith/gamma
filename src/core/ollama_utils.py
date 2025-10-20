"""
Utilities for Ollama integration.

Provides enhanced Ollama server detection, model discovery, and metadata parsing.
"""
import subprocess
import json
import requests
from typing import List, Dict, Any, Optional, Tuple


# Common Ollama ports to check
DEFAULT_OLLAMA_PORTS = [11434, 11435, 11436]


def detect_ollama_server(ports: List[int] = None) -> Optional[str]:
    """
    Auto-detect Ollama server on common ports.

    Args:
        ports: List of ports to check. If None, uses DEFAULT_OLLAMA_PORTS

    Returns:
        Base URL of running Ollama server, or None if not found
    """
    if ports is None:
        ports = DEFAULT_OLLAMA_PORTS

    for port in ports:
        url = f"http://localhost:{port}"
        try:
            response = requests.get(f"{url}/api/tags", timeout=2)
            if response.status_code == 200:
                return url
        except (requests.ConnectionError, requests.Timeout):
            continue

    return None


def is_ollama_installed() -> bool:
    """Check if Ollama CLI is installed and in PATH."""
    try:
        subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def list_ollama_models(base_url: str = None) -> List[Dict[str, Any]]:
    """
    List all available Ollama models with metadata.

    Args:
        base_url: Ollama server URL. If None, auto-detects.

    Returns:
        List of model dictionaries with name, size, modified time, etc.

    Raises:
        RuntimeError: If Ollama server is not accessible
    """
    if base_url is None:
        base_url = detect_ollama_server()
        if base_url is None:
            raise RuntimeError("Ollama server not found. Is it running?")

    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to list Ollama models: {e}")


def get_model_info(model_name: str, base_url: str = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific Ollama model.

    Args:
        model_name: Name of the model (e.g., "llama2", "mistral")
        base_url: Ollama server URL. If None, auto-detects.

    Returns:
        Dictionary with model metadata including:
        - modelfile: The modelfile content
        - parameters: Model parameters
        - template: Prompt template
        - details: Architecture details (family, parameter_size, quantization_level)

    Raises:
        RuntimeError: If model not found or server not accessible
    """
    if base_url is None:
        base_url = detect_ollama_server()
        if base_url is None:
            raise RuntimeError("Ollama server not found. Is it running?")

    try:
        response = requests.post(
            f"{base_url}/api/show",
            json={"name": model_name},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get model info for '{model_name}': {e}")


def parse_model_details(model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse model details from Ollama model info.

    Args:
        model_info: Model info dictionary from get_model_info()

    Returns:
        Parsed details including:
        - family: Model family (llama, mistral, etc.)
        - parameter_size: Model size (7B, 13B, etc.)
        - quantization: Quantization type (Q4_0, Q5_K_M, etc.)
        - format: Model format (usually "gguf")
    """
    details = model_info.get("details", {})

    return {
        "family": details.get("family", "unknown"),
        "parameter_size": details.get("parameter_size", "unknown"),
        "quantization_level": details.get("quantization_level", "unknown"),
        "format": details.get("format", "unknown"),
        "parameters": model_info.get("parameters", {}),
        "template": model_info.get("template", "")
    }


def check_model_availability(model_name: str, base_url: str = None) -> Tuple[bool, str]:
    """
    Check if a model is available in Ollama.

    Args:
        model_name: Name of the model to check
        base_url: Ollama server URL. If None, auto-detects.

    Returns:
        Tuple of (is_available: bool, message: str)
    """
    if base_url is None:
        base_url = detect_ollama_server()
        if base_url is None:
            return False, "Ollama server not found. Is it running?"

    try:
        models = list_ollama_models(base_url)
        # Keep full model names with tags (e.g., "gpt-oss:20b")
        model_names = [m.get("name", "") for m in models]

        # Also check without tags for partial matches
        model_names_no_tags = [m.split(":")[0] for m in model_names]

        # Check exact match first, then check without tag
        if model_name in model_names:
            return True, f"Model '{model_name}' is available"
        elif model_name.split(":")[0] in model_names_no_tags:
            # Partial match - model family exists
            matching = [m for m in model_names if m.startswith(model_name.split(":")[0])]
            return False, f"Model '{model_name}' not found, but similar: {', '.join(matching)}"
        else:
            available = ", ".join(model_names) if model_names else "none"
            return False, f"Model '{model_name}' not found. Available: {available}"

    except Exception as e:
        return False, f"Error checking model availability: {e}"


def suggest_ollama_models(hardware_type: str = "auto") -> List[Dict[str, str]]:
    """
    Suggest appropriate Ollama models based on hardware.

    Args:
        hardware_type: "cpu", "gpu", "apple_silicon", or "auto"

    Returns:
        List of suggested models with name, size, and description
    """
    # CPU-friendly models (smaller, quantized)
    cpu_models = [
        {"name": "phi", "size": "2.7B", "desc": "Small, fast model for CPU"},
        {"name": "tinyllama", "size": "1.1B", "desc": "Tiny but capable"},
        {"name": "gemma:2b", "size": "2B", "desc": "Google's small model"},
    ]

    # GPU-friendly models (larger, higher quality)
    gpu_models = [
        {"name": "llama2", "size": "7B", "desc": "Meta's Llama 2"},
        {"name": "mistral", "size": "7B", "desc": "Mistral AI's model"},
        {"name": "llama2:13b", "size": "13B", "desc": "Larger Llama 2"},
        {"name": "mixtral", "size": "47B", "desc": "Mixture of experts"},
    ]

    # Apple Silicon optimized
    apple_models = [
        {"name": "llama2", "size": "7B", "desc": "Works well with unified memory"},
        {"name": "mistral", "size": "7B", "desc": "Efficient on M1/M2/M3"},
        {"name": "codellama", "size": "7B", "desc": "Code generation"},
    ]

    if hardware_type == "cpu":
        return cpu_models
    elif hardware_type == "gpu":
        return gpu_models
    elif hardware_type == "apple_silicon":
        return apple_models
    else:  # auto
        return cpu_models + gpu_models[:2]  # Mix of small and medium


def format_model_size(size_bytes: int) -> str:
    """Format model size in bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def get_ollama_version() -> Optional[str]:
    """Get Ollama CLI version if installed."""
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        # Parse version from output like "ollama version is 0.1.17"
        output = result.stdout.strip()
        if "version" in output.lower():
            return output.split()[-1]
        return output
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
