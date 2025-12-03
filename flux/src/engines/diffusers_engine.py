"""
Hugging Face Diffusers engine implementation.

Provides full support for Stable Diffusion models with deep inspection capabilities.
"""

from typing import Any, Dict, List, Optional, Callable
from PIL import Image
import numpy as np
import torch
from diffusers import (
    StableDiffusionPipeline,
    DDPMScheduler,
    DDIMScheduler,
    PNDMScheduler,
    EulerDiscreteScheduler,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    DPMSolverSinglestepScheduler,
    HeunDiscreteScheduler,
    LMSDiscreteScheduler,
    UniPCMultistepScheduler,
)

from .base import DiffusionEngine, DiffusionConfig, DiffusionOutput, InspectionData


# Scheduler mapping
SCHEDULER_MAP = {
    "ddpm": DDPMScheduler,
    "ddim": DDIMScheduler,
    "pndm": PNDMScheduler,
    "euler": EulerDiscreteScheduler,
    "euler_ancestral": EulerAncestralDiscreteScheduler,
    "dpm": DPMSolverMultistepScheduler,
    "dpm++": DPMSolverSinglestepScheduler,
    "heun": HeunDiscreteScheduler,
    "lms": LMSDiscreteScheduler,
    "unipc": UniPCMultistepScheduler,
}


class DiffusersEngine(DiffusionEngine):
    """
    Hugging Face Diffusers implementation with full inspection support.

    Supports:
    - Text-to-image generation
    - Deep inspection at each denoising step
    - Multiple schedulers
    - Attention map extraction
    - VAE latent space visualization
    - U-Net activation inspection
    """

    def __init__(self, config: DiffusionConfig):
        super().__init__(config)
        self.device = None
        self._attention_maps: Dict[int, Dict[str, torch.Tensor]] = {}
        self._current_step = 0

    def load(self) -> None:
        """Load the Stable Diffusion pipeline."""
        self.log_info(f"Loading model: {self.config.model_name}")

        # Determine device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        self.log_info(f"Using device: {self.device}")

        # Load pipeline
        dtype = torch.float16 if self.config.use_fp16 and self.device != "cpu" else torch.float32

        try:
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.config.model_name,
                torch_dtype=dtype,
                safety_checker=None,  # Disable for educational use
                requires_safety_checker=False,
            )
            self.pipeline = self.pipeline.to(self.device)

            # Set scheduler
            self.set_scheduler(self.config.scheduler_type)

            # Enable optimizations
            if self.config.attention_slicing:
                self.pipeline.enable_attention_slicing()

            if self.config.xformers and self.device == "cuda":
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                except Exception as e:
                    self.log_warning(f"xformers not available: {e}")

            self.model = self.pipeline  # For base class compatibility

            self.log_info("Model loaded successfully")

        except Exception as e:
            self.log_error(f"Failed to load model: {e}")
            raise

    def unload(self) -> None:
        """Unload the model from memory."""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self.model = None

        if self.device in ["cuda", "mps"]:
            if self.device == "cuda":
                torch.cuda.empty_cache()
            elif self.device == "mps":
                torch.mps.empty_cache()

        self.log_info("Model unloaded")

    def get_device(self) -> str:
        """Get device type."""
        return self.device or "cpu"

    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> DiffusionOutput:
        """Generate image from text prompt (fast, no inspection)."""
        self._ensure_model_loaded()

        # Use config defaults if not specified
        steps = num_inference_steps or self.config.num_inference_steps
        scale = guidance_scale or self.config.guidance_scale
        neg_prompt = negative_prompt or self.config.negative_prompt

        # Set seed for reproducibility
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        self.log_debug(f"Generating: '{prompt}' ({steps} steps, scale={scale})")

        # Generate
        output = self.pipeline(
            prompt=prompt,
            negative_prompt=neg_prompt,
            num_inference_steps=steps,
            guidance_scale=scale,
            generator=generator,
            height=self.config.height,
            width=self.config.width,
            **kwargs
        )

        image = output.images[0]

        return DiffusionOutput(
            image=image,
            prompt=prompt,
            negative_prompt=neg_prompt,
            seed=seed,
            num_steps=steps,
            guidance_scale=scale,
            scheduler_type=self.config.scheduler_type,
            inspection_data=[],
            metadata={"device": self.device}
        )

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
        Generate image with full inspection at specified steps.

        This is the core method for educational visualization.
        """
        self._ensure_model_loaded()

        steps = num_inference_steps or self.config.num_inference_steps
        scale = guidance_scale or self.config.guidance_scale
        neg_prompt = negative_prompt or self.config.negative_prompt

        # Determine which steps to inspect
        if inspect_steps is None:
            # Inspect all steps by default
            steps_to_inspect = set(range(steps))
        else:
            steps_to_inspect = set(inspect_steps)

        # Set seed
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        self.log_debug(f"Generating with inspection: '{prompt}' (inspecting {len(steps_to_inspect)} steps)")

        # Storage for inspection data
        inspection_data: List[InspectionData] = []

        # Custom callback to capture inspection data
        def inspection_callback(pipe, step_index, timestep, callback_kwargs):
            """Callback executed at each denoising step."""
            self._current_step = step_index

            if step_index in steps_to_inspect:
                # Extract data for inspection
                latents = callback_kwargs.get("latents")

                # Create inspection data object
                data = InspectionData(
                    step=step_index,
                    timestep=float(timestep),
                )

                # Capture latent
                if latents is not None:
                    data.latent_current = latents.cpu().numpy()

                # Capture scheduler state
                data.scheduler_state = {
                    "timestep": float(timestep),
                    "step_index": step_index,
                    "num_inference_steps": steps,
                }

                # Decode intermediate image (expensive, but educational!)
                if latents is not None:
                    try:
                        with torch.no_grad():
                            # Decode latent to image
                            latents_decoded = 1 / 0.18215 * latents
                            image_tensor = self.pipeline.vae.decode(latents_decoded).sample
                            image_tensor = (image_tensor / 2 + 0.5).clamp(0, 1)
                            image_np = image_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
                            image_np = (image_np * 255).astype(np.uint8)
                            data.intermediate_image = Image.fromarray(image_np)
                    except Exception as e:
                        self.log_warning(f"Failed to decode intermediate image: {e}")

                # Store inspection data
                inspection_data.append(data)

                # Call user hooks
                self._call_inspection_hooks(step_index, data)

            return callback_kwargs

        # Generate with callback
        output = self.pipeline(
            prompt=prompt,
            negative_prompt=neg_prompt,
            num_inference_steps=steps,
            guidance_scale=scale,
            generator=generator,
            height=self.config.height,
            width=self.config.width,
            callback_on_step_end=inspection_callback,
        )

        image = output.images[0]

        return DiffusionOutput(
            image=image,
            prompt=prompt,
            negative_prompt=neg_prompt,
            seed=seed,
            num_steps=steps,
            guidance_scale=scale,
            scheduler_type=self.config.scheduler_type,
            inspection_data=inspection_data,
            metadata={
                "device": self.device,
                "inspection_steps": len(inspection_data),
            }
        )

    def encode_image(self, image: Image.Image) -> np.ndarray:
        """Encode PIL image to latent space."""
        self._ensure_model_loaded()

        # Resize if needed
        if image.size != (self.config.width, self.config.height):
            image = image.resize((self.config.width, self.config.height))

        # Convert to tensor
        image_np = np.array(image).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np).permute(2, 0, 1).unsqueeze(0)
        image_tensor = image_tensor.to(self.device, dtype=torch.float16 if self.config.use_fp16 else torch.float32)

        # Normalize to [-1, 1]
        image_tensor = 2.0 * image_tensor - 1.0

        # Encode
        with torch.no_grad():
            latent_dist = self.pipeline.vae.encode(image_tensor).latent_dist
            latent = latent_dist.sample()
            latent = 0.18215 * latent

        return latent.cpu().numpy()

    def decode_latent(self, latent: np.ndarray) -> Image.Image:
        """Decode latent array to PIL image."""
        self._ensure_model_loaded()

        # Convert to tensor
        latent_tensor = torch.from_numpy(latent).to(
            self.device,
            dtype=torch.float16 if self.config.use_fp16 else torch.float32
        )

        # Decode
        with torch.no_grad():
            latent_tensor = 1 / 0.18215 * latent_tensor
            image_tensor = self.pipeline.vae.decode(latent_tensor).sample
            image_tensor = (image_tensor / 2 + 0.5).clamp(0, 1)

        # Convert to PIL
        image_np = image_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
        image_np = (image_np * 255).astype(np.uint8)

        return Image.fromarray(image_np)

    def get_scheduler_info(self) -> Dict[str, Any]:
        """Get information about current scheduler."""
        if self.pipeline is None:
            return {}

        scheduler = self.pipeline.scheduler

        return {
            "type": scheduler.__class__.__name__,
            "num_train_timesteps": scheduler.config.num_train_timesteps,
            "beta_start": scheduler.config.beta_start,
            "beta_end": scheduler.config.beta_end,
            "beta_schedule": scheduler.config.beta_schedule,
        }

    def set_scheduler(self, scheduler_type: str):
        """Change the noise scheduler."""
        if scheduler_type not in SCHEDULER_MAP:
            available = ", ".join(SCHEDULER_MAP.keys())
            raise ValueError(
                f"Unknown scheduler '{scheduler_type}'. Available: {available}"
            )

        if self.pipeline is None:
            # Just update config
            self.config.scheduler_type = scheduler_type
            return

        # Get current scheduler config
        scheduler_config = self.pipeline.scheduler.config

        # Create new scheduler
        scheduler_class = SCHEDULER_MAP[scheduler_type]
        self.pipeline.scheduler = scheduler_class.from_config(scheduler_config)

        self.config.scheduler_type = scheduler_type
        self.log_debug(f"Scheduler changed to: {scheduler_type}")

    def get_available_schedulers(self) -> List[str]:
        """Get list of available scheduler types."""
        return list(SCHEDULER_MAP.keys())

    def extract_cross_attention(
        self,
        prompt: str,
        step: int
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Extract cross-attention maps.

        Note: This requires hooking into the U-Net forward pass,
        which is more complex. For now, returns None.

        TODO: Implement attention extraction using hooks.
        """
        # This would require registering forward hooks on attention layers
        # and capturing the attention weights during generation.
        # Implementation is possible but complex - left for future enhancement.
        return None

    def get_attention_map_for_token(
        self,
        prompt: str,
        token_index: int,
        step: int
    ) -> Optional[np.ndarray]:
        """Get attention map for specific token."""
        # Similar to extract_cross_attention, requires hooks
        return None

    def get_engine_specific_config(self) -> Dict[str, Any]:
        """Get Diffusers-specific configuration."""
        return {
            "pipeline_type": "StableDiffusionPipeline",
            "scheduler": self.config.scheduler_type,
            "use_fp16": self.config.use_fp16,
            "attention_slicing": self.config.attention_slicing,
            "xformers": self.config.xformers,
        }
