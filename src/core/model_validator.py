"""
Model and engine validation utilities.

Prevents invalid combinations like:
- Using pytorch engine with GGUF files
- Using llamacpp engine with HuggingFace model IDs
- Using ollama engine for mind melding
"""

import os
import re
from typing import Tuple, Optional, List
from dataclasses import dataclass

from src.engines.capability_registry import (
    ENGINES,
    list_engines,
    list_engines_with,
    get_mind_meld_compatible_engines,
)

@dataclass
class ValidationResult:
    """Result of model/engine validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    suggestion: Optional[str] = None


class ModelValidator:
    """Validates engine and model combinations."""

    # Model format patterns
    GGUF_PATTERN = re.compile(r'\.gguf$', re.IGNORECASE)
    ONNX_PATTERN = re.compile(r'\.onnx$', re.IGNORECASE)
    HUGGINGFACE_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+$')
    OLLAMA_PATTERN = re.compile(r'^[a-z0-9_-]+(?::[a-z0-9._-]+)?$', re.IGNORECASE)

    # Engine categorization (derived from capability registry)
    NATIVE_ENGINES = {
        name for name, info in ENGINES.items()
        if info.capabilities.engine_type == "native"
    }
    WRAPPER_ENGINES = {
        name for name, info in ENGINES.items()
        if info.capabilities.engine_type == "wrapper"
    }

    # Legacy aliases for compatibility
    ENGINES_WITH_LOGITS = {
        name for name, info in ENGINES.items()
        if info.capabilities.supports_logits
    }
    ENGINES_WITHOUT_LOGITS = set(ENGINES) - ENGINES_WITH_LOGITS

    CUDA_ONLY_ENGINES = {'vllm', 'pytorch_cuda'}
    APPLE_ONLY_ENGINES = {'mlx', 'mlx_gpu'}

    @staticmethod
    def format_logits_requirement(engine: str, use_case: str, mind_meld: bool = False) -> Tuple[str, str]:
        """
        Format a standardized message for engines that do not expose logits.

        Returns:
            (error_message, detail_message). Empty strings when logits are supported.
        """
        engine_lower = engine.lower()
        info = ENGINES.get(engine_lower)
        if info and info.capabilities.supports_logits:
            return "", ""

        no_logits = sorted(list_engines_with(supports_logits=False))
        if mind_meld:
            suggestions = sorted(get_mind_meld_compatible_engines())
        else:
            suggestions = sorted(list_engines_with(supports_logits=True))

        error = f"{use_case} requires real logits. Engine '{engine}' does not expose logits."
        detail = (
            f"Engines without logits: {', '.join(no_logits)}. "
            f"Use a native engine with logits: {', '.join(suggestions)}."
        )
        return error, detail

    @staticmethod
    def is_wrapper_engine(engine: str) -> bool:
        """Check if engine is a wrapper (limited logits access)."""
        return engine.lower() in ModelValidator.WRAPPER_ENGINES

    @staticmethod
    def is_native_engine(engine: str) -> bool:
        """Check if engine is native (full logits access)."""
        return engine.lower() in ModelValidator.NATIVE_ENGINES

    @staticmethod
    def detect_model_format(model_identifier: str) -> str:
        """
        Detect the format of a model identifier.

        Returns:
            'gguf', 'onnx', 'huggingface', 'ollama', 'path', or 'unknown'
        """
        # Check if it's a file path
        if os.path.exists(model_identifier):
            if ModelValidator.GGUF_PATTERN.search(model_identifier):
                return 'gguf'
            elif ModelValidator.ONNX_PATTERN.search(model_identifier):
                return 'onnx'
            else:
                return 'path'

        # Check patterns
        if ModelValidator.GGUF_PATTERN.search(model_identifier):
            return 'gguf'
        elif ModelValidator.ONNX_PATTERN.search(model_identifier):
            return 'onnx'
        elif ModelValidator.HUGGINGFACE_PATTERN.match(model_identifier):
            return 'huggingface'
        elif ModelValidator.OLLAMA_PATTERN.match(model_identifier):
            return 'ollama'

        return 'unknown'

    @staticmethod
    def validate_engine_model_combination(
        engine: str,
        model_identifier: str,
        require_logits: bool = False
    ) -> ValidationResult:
        """
        Validate that an engine can load a specific model.

        Args:
            engine: Engine name (e.g., 'pytorch', 'llamacpp')
            model_identifier: Model path or ID
            require_logits: If True, warn about engines without logits access

        Returns:
            ValidationResult with validation status and messages
        """
        engine_lower = engine.lower()
        model_format = ModelValidator.detect_model_format(model_identifier)

        # Check engine + format compatibility
        if engine_lower in ['pytorch', 'pytorch_cuda', 'vllm', 'mlx', 'mlx_gpu', 'jax', 'tensorflow']:
            if model_format == 'gguf':
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine '{engine}' cannot load GGUF files",
                    suggestion=f"Use 'llamacpp' engine for GGUF files: llamacpp:{model_identifier}"
                )
            elif model_format == 'onnx':
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine '{engine}' cannot load ONNX files",
                    suggestion=f"Use 'onnx' engine for ONNX files: onnx:{model_identifier}"
                )
            elif model_format == 'ollama':
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine '{engine}' cannot load Ollama models directly",
                    suggestion=f"Use HuggingFace model ID (org/model-name) or use 'ollama' engine: ollama:{model_identifier}"
                )
            elif model_format not in ['huggingface', 'unknown']:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine '{engine}' expects HuggingFace model IDs (org/model-name)",
                    suggestion="Use format like: pytorch:google/gemma-2-2b-it"
                )

        elif engine_lower == 'llamacpp':
            if model_format == 'huggingface':
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine 'llamacpp' cannot load HuggingFace models directly",
                    suggestion=f"Download GGUF version or convert to GGUF first. See docs/ENGINE_ARCHITECTURE.md"
                )
            elif model_format != 'gguf' and model_format != 'path':
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine 'llamacpp' expects GGUF files (.gguf)",
                    suggestion="Use format like: llamacpp:./models/model.gguf"
                )

        elif engine_lower == 'onnx':
            if model_format != 'onnx' and model_format != 'path':
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine 'onnx' expects ONNX files (.onnx)",
                    suggestion="Use format like: onnx:./models/model.onnx --onnx-tokenizer org/model"
                )

        elif engine_lower == 'ollama':
            if model_format not in ['ollama', 'unknown']:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine 'ollama' expects Ollama model names",
                    suggestion=f"Use format like: ollama:llama2 or ollama:gemma2:2b"
                )

            # Warn about logits if required
            if require_logits:
                return ValidationResult(
                    is_valid=False,
                    error_message="Ollama engine does not provide logits access (HTTP API only)",
                    suggestion="For mind melding with real logits, use 'llamacpp' engine with GGUF file instead"
                )

        elif engine_lower == 'huggingface_inference':
            # HuggingFace Inference API expects HuggingFace model IDs
            if model_format not in ['huggingface', 'unknown']:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Engine 'huggingface_inference' expects HuggingFace model IDs (org/model-name)",
                    suggestion=f"Use format like: huggingface_inference:meta-llama/Llama-2-7b-chat-hf"
                )

            # Warn about logits if required
            if require_logits:
                return ValidationResult(
                    is_valid=False,
                    error_message="HuggingFace Inference API does not provide logits access (HTTP API only)",
                    suggestion="For mind melding with real logits, use 'pytorch' or 'vllm' engine instead"
                )

        elif engine_lower == 'openai':
            # OpenAI API accepts any model name (gpt-4, gpt-3.5-turbo, etc.)
            # No strict validation needed for model format

            # Warn about logits if required
            if require_logits:
                return ValidationResult(
                    is_valid=False,
                    error_message="OpenAI API does not provide logits access (HTTP API only)",
                    suggestion="For mind melding with real logits, use a native engine like 'pytorch' or 'vllm'"
                )

        # Check logits requirement
        if require_logits and engine_lower in ModelValidator.ENGINES_WITHOUT_LOGITS:
            return ValidationResult(
                is_valid=False,
                error_message=f"Engine '{engine}' does not provide logits access",
                suggestion="Mind melding requires engines with logits access."
            )

        return ValidationResult(is_valid=True)

    @staticmethod
    def validate_hardware_compatibility(engine: str) -> ValidationResult:
        """
        Check if the engine is compatible with current hardware.

        Args:
            engine: Engine name

        Returns:
            ValidationResult with warnings about hardware compatibility
        """
        engine_lower = engine.lower()

        # Check CUDA engines
        if engine_lower in ModelValidator.CUDA_ONLY_ENGINES:
            try:
                import torch
                if not torch.cuda.is_available():
                    return ValidationResult(
                        is_valid=True,
                        warning_message=f"⚠️  Engine '{engine}' requires CUDA but CUDA is not available",
                        suggestion="Use 'pytorch' or 'llamacpp' engine for CPU/other hardware"
                    )
            except ImportError:
                return ValidationResult(
                    is_valid=True,
                    warning_message=f"⚠️  Cannot check CUDA availability (torch not installed)",
                    suggestion="Install torch to verify CUDA support"
                )

        # Check Apple Silicon engines
        if engine_lower in ModelValidator.APPLE_ONLY_ENGINES:
            import platform
            if not (platform.system() == "Darwin" and platform.machine().startswith("arm")):
                return ValidationResult(
                    is_valid=True,
                    warning_message=f"⚠️  Engine '{engine}' is optimized for Apple Silicon but you're on {platform.system()} {platform.machine()}",
                    suggestion="Use 'pytorch' or 'llamacpp' engine for better compatibility"
                )

        return ValidationResult(is_valid=True)

    @staticmethod
    def validate_model_spec(
        model_spec: str,
        require_logits: bool = False
    ) -> ValidationResult:
        """
        Validate a complete model specification (engine:model format).

        Args:
            model_spec: Full model spec like "pytorch:google/gemma-2-2b-it"
            require_logits: If True, warn about engines without logits

        Returns:
            ValidationResult
        """
        if ':' not in model_spec:
            return ValidationResult(
                is_valid=False,
                error_message="Model specification must be in format 'engine:model'",
                suggestion="Examples: pytorch:google/gemma-2-2b-it, llamacpp:./models/model.gguf"
            )

        parts = model_spec.split(':', 1)
        if len(parts) != 2:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid model specification format",
                suggestion="Use format: engine:model"
            )

        engine, model = parts

        # Validate engine exists
        supported_engines = list_engines()
        if engine.lower() not in supported_engines:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unknown engine '{engine}'",
                suggestion=f"Supported engines: {', '.join(supported_engines)}"
            )

        # Validate engine + model combination
        result = ModelValidator.validate_engine_model_combination(
            engine, model, require_logits
        )
        if not result.is_valid:
            return result

        # Validate hardware compatibility
        hw_result = ModelValidator.validate_hardware_compatibility(engine)
        if hw_result.warning_message:
            return ValidationResult(
                is_valid=True,
                warning_message=hw_result.warning_message,
                suggestion=hw_result.suggestion
            )

        return result

    @staticmethod
    def suggest_engine_for_model(model_identifier: str) -> List[str]:
        """
        Suggest appropriate engines for a given model.

        Args:
            model_identifier: Model path or ID

        Returns:
            List of suggested engine names
        """
        model_format = ModelValidator.detect_model_format(model_identifier)

        if model_format == 'gguf':
            return ['llamacpp']
        elif model_format == 'onnx':
            return ['onnx']
        elif model_format == 'huggingface':
            # Detect hardware
            suggestions = ['pytorch']
            try:
                import torch
                if torch.cuda.is_available():
                    suggestions = ['vllm', 'pytorch_cuda', 'pytorch']
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    suggestions = ['mlx_gpu', 'pytorch']
            except ImportError:
                pass
            return suggestions
        elif model_format == 'ollama':
            return ['ollama']

        return ['pytorch']  # Default fallback


def print_validation_result(result: ValidationResult, model_spec: str = ""):
    """Pretty print a validation result."""
    if not result.is_valid:
        print(f"\n❌ Invalid configuration: {model_spec}")
        print(f"   {result.error_message}")
        if result.suggestion:
            print(f"   💡 Suggestion: {result.suggestion}")
        print()
        return False

    if result.warning_message:
        print(f"\n{result.warning_message}")
        if result.suggestion:
            print(f"   💡 Suggestion: {result.suggestion}")
        print()

    return True
