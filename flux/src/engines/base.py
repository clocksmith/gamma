"""
Abstract base class for diffusion model engines.

Extends gamma-core's ModelEngine with diffusion-specific functionality.
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from PIL import Image
import numpy as np

import sys
sys.path.insert(0, '/home/clocksmith/deco/gamma-core')
from gamma_core.engine import ModelEngine, EngineConfig


@dataclass
class DiffusionConfig(EngineConfig):
    """Configuration for diffusion model engines."""

    # Image generation parameters
    height: int = 512
    width: int = 512
    num_inference_steps: int = 50
    guidance_scale: float = 7.5
    negative_prompt: Optional[str] = None

    # Scheduler
    scheduler_type: str = "pndm"

    # Performance
    use_fp16: bool = True
    attention_slicing: bool = True
    xformers: bool = False

    # Inspection
    enable_inspection: bool = True
    inspect_steps: List[int] = field(default_factory=list)  # Empty = all steps


@dataclass
class InspectionData:
    """
    Deep inspection data for a single diffusion step.

    Captures internals of the denoising process for educational purposes.
    """

    step: int
    timestep: float

    # Latent representations
    latent_current: Optional[np.ndarray] = None  # Current latent
    latent_noise_pred: Optional[np.ndarray] = None  # Predicted noise

    # Guidance components (for classifier-free guidance)
    noise_pred_uncond: Optional[np.ndarray] = None  # Unconditional prediction
    noise_pred_cond: Optional[np.ndarray] = None  # Conditional prediction

    # Attention maps (if available)
    cross_attention_maps: Optional[Dict[str, np.ndarray]] = None
    self_attention_maps: Optional[Dict[str, np.ndarray]] = None

    # U-Net activations (if available)
    unet_activations: Optional[Dict[str, np.ndarray]] = None

    # Scheduler state
    scheduler_state: Optional[Dict[str, Any]] = None

    # Intermediate image (decoded from latent)
    intermediate_image: Optional[Image.Image] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffusionOutput:
    """Output from a diffusion generation."""

    # Final output
    image: Image.Image

    # Generation parameters
    prompt: str
    negative_prompt: Optional[str]
    seed: Optional[int]
    num_steps: int
    guidance_scale: float
    scheduler_type: str

    # Inspection data (if enabled)
    inspection_data: List[InspectionData] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class DiffusionEngine(ModelEngine):
    """
    Abstract base class for diffusion model engines.

    Extends gamma-core's ModelEngine with diffusion-specific methods:
    - Text-to-image generation
    - Image-to-image generation
    - Inpainting
    - Deep inspection of denoising process
    """

    def __init__(self, config: DiffusionConfig):
        super().__init__(config)
        self.config: DiffusionConfig = config
        self.pipeline: Any = None
        self._inspection_enabled = config.enable_inspection
        self._inspection_hooks: List[Callable] = []

    # ========================================================================
    # Core Abstract Methods - Diffusion-specific
    # ========================================================================

    @abstractmethod
    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> DiffusionOutput:
        """
        Generate an image from text prompt.

        Args:
            prompt: Text description of desired image
            negative_prompt: What to avoid in generation
            num_inference_steps: Number of denoising steps
            guidance_scale: Classifier-free guidance scale
            seed: Random seed for reproducibility
            **kwargs: Additional generation parameters

        Returns:
            DiffusionOutput with image and inspection data
        """
        pass

    @abstractmethod
    def generate_with_inspection(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        inspect_steps: Optional[List[int]] = None,
    ) -> DiffusionOutput:
        """
        Generate image with full inspection data at specified steps.

        Args:
            prompt: Text description
            negative_prompt: What to avoid
            num_inference_steps: Number of steps
            guidance_scale: CFG scale
            seed: Random seed
            inspect_steps: Which steps to inspect (None = all)

        Returns:
            DiffusionOutput with detailed inspection data
        """
        pass

    @abstractmethod
    def encode_image(self, image: Image.Image) -> np.ndarray:
        """
        Encode image to latent space.

        Args:
            image: PIL Image to encode

        Returns:
            Latent representation as numpy array
        """
        pass

    @abstractmethod
    def decode_latent(self, latent: np.ndarray) -> Image.Image:
        """
        Decode latent representation to image.

        Args:
            latent: Latent array to decode

        Returns:
            PIL Image
        """
        pass

    @abstractmethod
    def get_scheduler_info(self) -> Dict[str, Any]:
        """Get information about the current scheduler."""
        pass

    @abstractmethod
    def set_scheduler(self, scheduler_type: str):
        """Change the noise scheduler."""
        pass

    @abstractmethod
    def get_available_schedulers(self) -> List[str]:
        """Get list of available scheduler types."""
        pass

    # ========================================================================
    # Inspection and Debugging
    # ========================================================================

    def enable_inspection(self):
        """Enable deep inspection of diffusion process."""
        self._inspection_enabled = True

    def disable_inspection(self):
        """Disable inspection to improve performance."""
        self._inspection_enabled = False

    def is_inspection_enabled(self) -> bool:
        """Check if inspection is enabled."""
        return self._inspection_enabled

    def register_inspection_hook(self, hook: Callable):
        """
        Register a custom inspection hook.

        Hook signature: hook(step: int, data: InspectionData) -> None
        """
        self._inspection_hooks.append(hook)

    def clear_inspection_hooks(self):
        """Clear all inspection hooks."""
        self._inspection_hooks.clear()

    def _call_inspection_hooks(self, step: int, data: InspectionData):
        """Call all registered inspection hooks."""
        for hook in self._inspection_hooks:
            try:
                hook(step, data)
            except Exception as e:
                self.log_warning(f"Inspection hook failed: {e}")

    # ========================================================================
    # Attention Extraction (to be implemented by subclasses)
    # ========================================================================

    def extract_cross_attention(
        self,
        prompt: str,
        step: int
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Extract cross-attention maps at a specific step.

        Override in subclasses that support attention extraction.

        Args:
            prompt: Text prompt
            step: Denoising step number

        Returns:
            Dictionary mapping attention layer names to attention maps
        """
        return None

    def get_attention_map_for_token(
        self,
        prompt: str,
        token_index: int,
        step: int
    ) -> Optional[np.ndarray]:
        """
        Get attention map for a specific token.

        Override in subclasses that support per-token attention.

        Args:
            prompt: Text prompt
            token_index: Index of token in prompt
            step: Denoising step number

        Returns:
            2D attention map as numpy array
        """
        return None

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_latent_shape(self) -> Tuple[int, int, int, int]:
        """
        Get the shape of latent tensors.

        Returns:
            Tuple of (batch, channels, height, width)
        """
        # Default: 4 channels (for Stable Diffusion VAE)
        # Height and width are typically image_size / 8
        latent_h = self.config.height // 8
        latent_w = self.config.width // 8
        return (1, 4, latent_h, latent_w)

    def estimate_memory_usage(self) -> Dict[str, float]:
        """
        Estimate memory usage for current configuration.

        Returns:
            Dictionary with memory estimates in MB
        """
        # Rough estimates for Stable Diffusion models
        latent_h, latent_w = self.config.height // 8, self.config.width // 8

        estimates = {
            "model_params_mb": 3500,  # ~3.5GB for SD 2.1
            "latent_mb": (4 * latent_h * latent_w * 4) / 1024 / 1024,  # FP32
            "intermediate_mb": 500,  # Intermediate activations
        }

        if self.config.use_fp16:
            estimates["model_params_mb"] /= 2

        estimates["total_mb"] = sum(estimates.values())

        return estimates

    def get_generation_config(self) -> Dict[str, Any]:
        """Get current generation configuration."""
        return {
            "height": self.config.height,
            "width": self.config.width,
            "num_inference_steps": self.config.num_inference_steps,
            "guidance_scale": self.config.guidance_scale,
            "scheduler": self.config.scheduler_type,
            "use_fp16": self.config.use_fp16,
        }

    # Override from base class
    def predict(self, inputs: Any, **kwargs) -> Dict[str, Any]:
        """
        Generic predict method (from ModelEngine base class).

        For diffusion, redirects to generate().
        """
        if isinstance(inputs, str):
            output = self.generate(inputs, **kwargs)
            return {
                "image": output.image,
                "inspection_data": output.inspection_data,
            }
        else:
            raise ValueError("Diffusion engines expect string prompts as input")
