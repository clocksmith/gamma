"""
Attention map extraction and visualization.

Provides tools to extract and visualize cross-attention maps from
diffusion models, showing how text tokens influence different image regions.
"""

from typing import Dict, List, Optional, Tuple, Callable
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from torch import nn


class AttentionExtractor:
    """
    Extract attention maps from U-Net during diffusion.

    Uses forward hooks to capture cross-attention weights between
    text embeddings and image regions.
    """

    def __init__(self, unet: nn.Module):
        """
        Initialize attention extractor.

        Args:
            unet: U-Net model from diffusion pipeline
        """
        self.unet = unet
        self.attention_maps: Dict[str, torch.Tensor] = {}
        self.hooks: List[torch.utils.hooks.RemovableHandle] = []
        self._enabled = False

    def enable(self):
        """Enable attention extraction by registering hooks."""
        if self._enabled:
            return

        self._register_hooks()
        self._enabled = True

    def disable(self):
        """Disable attention extraction by removing hooks."""
        if not self._enabled:
            return

        self._remove_hooks()
        self._enabled = False
        self.attention_maps.clear()

    def _register_hooks(self):
        """Register forward hooks on attention layers."""
        # Find all attention layers in U-Net
        for name, module in self.unet.named_modules():
            # Look for cross-attention layers
            # Different architectures may have different naming
            if "attn2" in name or "cross_attn" in name:
                hook = module.register_forward_hook(
                    self._make_attention_hook(name)
                )
                self.hooks.append(hook)

    def _remove_hooks(self):
        """Remove all registered hooks."""
        for hook in self.hooks:
            hook.remove()
        self.hooks.clear()

    def _make_attention_hook(self, layer_name: str) -> Callable:
        """
        Create a hook function for a specific layer.

        Args:
            layer_name: Name of the attention layer

        Returns:
            Hook function
        """
        def hook(module, input, output):
            """Forward hook to capture attention weights."""
            # Attention weights are typically in module.attn_weights or similar
            if hasattr(module, "attn_weights"):
                self.attention_maps[layer_name] = module.attn_weights.detach()
            elif isinstance(output, tuple) and len(output) > 1:
                # Some implementations return (output, attention_weights)
                self.attention_maps[layer_name] = output[1].detach()

        return hook

    def get_attention_maps(self) -> Dict[str, np.ndarray]:
        """
        Get captured attention maps as numpy arrays.

        Returns:
            Dictionary mapping layer names to attention maps
        """
        return {
            name: attn.cpu().numpy()
            for name, attn in self.attention_maps.items()
        }

    def get_aggregated_attention(
        self,
        method: str = "mean"
    ) -> Optional[np.ndarray]:
        """
        Aggregate attention across all layers.

        Args:
            method: Aggregation method ('mean', 'max', 'sum')

        Returns:
            Aggregated attention map or None if no maps available
        """
        if not self.attention_maps:
            return None

        maps = []
        for attn in self.attention_maps.values():
            # Normalize shape to (batch, heads, height*width, seq_len)
            if attn.ndim == 4:
                b, h, hw, s = attn.shape
                maps.append(attn)
            elif attn.ndim == 3:
                # Add batch dimension
                maps.append(attn.unsqueeze(0))

        if not maps:
            return None

        # Stack and aggregate
        stacked = torch.stack(maps, dim=0)  # (layers, batch, heads, hw, seq)

        if method == "mean":
            aggregated = stacked.mean(dim=0)  # Average across layers
        elif method == "max":
            aggregated = stacked.max(dim=0)[0]
        elif method == "sum":
            aggregated = stacked.sum(dim=0)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

        return aggregated.cpu().numpy()

    def get_attention_for_token(
        self,
        token_index: int,
        spatial_size: Tuple[int, int] = (64, 64)
    ) -> Optional[np.ndarray]:
        """
        Get attention map for a specific text token.

        Args:
            token_index: Index of the text token
            spatial_size: Target spatial resolution (H, W)

        Returns:
            2D attention map (H, W) or None if no maps available
        """
        aggregated = self.get_aggregated_attention(method="mean")

        if aggregated is None:
            return None

        # Shape: (batch, heads, height*width, seq_len)
        b, h, hw, s = aggregated.shape

        if token_index >= s:
            return None

        # Extract attention for this token and average across heads
        token_attn = aggregated[0, :, :, token_index]  # (heads, hw)
        token_attn = token_attn.mean(axis=0)  # (hw,)

        # Reshape to spatial dimensions
        side = int(np.sqrt(hw))
        token_attn = token_attn.reshape(side, side)

        # Resize to target resolution
        from scipy.ndimage import zoom
        scale_h = spatial_size[0] / side
        scale_w = spatial_size[1] / side

        if scale_h != 1.0 or scale_w != 1.0:
            token_attn = zoom(token_attn, (scale_h, scale_w), order=1)

        # Normalize to [0, 1]
        token_attn = (token_attn - token_attn.min()) / (token_attn.max() - token_attn.min() + 1e-8)

        return token_attn


class AttentionVisualizer:
    """
    Visualize attention maps as heatmaps overlaid on images.

    Provides educational visualizations showing how different text tokens
    influence different image regions.
    """

    @staticmethod
    def create_heatmap(
        attention_map: np.ndarray,
        colormap: str = "jet"
    ) -> Image.Image:
        """
        Create a heatmap visualization of attention.

        Args:
            attention_map: 2D attention array (H, W)
            colormap: Matplotlib colormap name

        Returns:
            PIL Image of the heatmap
        """
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm

        # Normalize
        attention_map = (attention_map - attention_map.min()) / (attention_map.max() - attention_map.min() + 1e-8)

        # Apply colormap
        cmap = cm.get_cmap(colormap)
        colored = cmap(attention_map)

        # Convert to uint8
        colored_uint8 = (colored[:, :, :3] * 255).astype(np.uint8)

        return Image.fromarray(colored_uint8)

    @staticmethod
    def overlay_heatmap(
        image: Image.Image,
        attention_map: np.ndarray,
        alpha: float = 0.5,
        colormap: str = "jet"
    ) -> Image.Image:
        """
        Overlay attention heatmap on image.

        Args:
            image: Base image
            attention_map: 2D attention array
            alpha: Overlay transparency (0=transparent, 1=opaque)
            colormap: Matplotlib colormap name

        Returns:
            PIL Image with heatmap overlay
        """
        # Resize attention map to match image
        from scipy.ndimage import zoom

        h, w = image.size[1], image.size[0]
        attn_h, attn_w = attention_map.shape

        if attn_h != h or attn_w != w:
            scale_h = h / attn_h
            scale_w = w / attn_w
            attention_map = zoom(attention_map, (scale_h, scale_w), order=1)

        # Create heatmap
        heatmap = AttentionVisualizer.create_heatmap(attention_map, colormap)

        # Resize heatmap to match image
        heatmap = heatmap.resize(image.size, Image.LANCZOS)

        # Blend
        blended = Image.blend(image, heatmap, alpha)

        return blended

    @staticmethod
    def create_token_attention_grid(
        image: Image.Image,
        tokens: List[str],
        attention_maps: List[np.ndarray],
        grid_size: Optional[Tuple[int, int]] = None
    ) -> Image.Image:
        """
        Create a grid showing attention for each token.

        Args:
            image: Base image
            tokens: List of text tokens
            attention_maps: List of attention maps (one per token)
            grid_size: (rows, cols) for grid layout (auto if None)

        Returns:
            PIL Image with grid of attention visualizations
        """
        n = len(tokens)

        if grid_size is None:
            # Auto-calculate grid size
            cols = int(np.ceil(np.sqrt(n)))
            rows = int(np.ceil(n / cols))
        else:
            rows, cols = grid_size

        # Create grid
        cell_w, cell_h = image.size
        grid_w = cols * cell_w
        grid_h = rows * cell_h

        grid = Image.new("RGB", (grid_w, grid_h), color=(255, 255, 255))
        draw = ImageDraw.Draw(grid)

        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()

        # Fill grid
        for i, (token, attn_map) in enumerate(zip(tokens, attention_maps)):
            if i >= rows * cols:
                break

            row = i // cols
            col = i % cols

            # Create overlay
            overlay = AttentionVisualizer.overlay_heatmap(image, attn_map, alpha=0.6)

            # Paste into grid
            x = col * cell_w
            y = row * cell_h
            grid.paste(overlay, (x, y))

            # Draw token label
            draw.text((x + 10, y + 10), token, fill=(255, 255, 255), font=font)

        return grid

    @staticmethod
    def create_animation(
        images: List[Image.Image],
        output_path: str,
        duration: int = 200
    ):
        """
        Create an animated GIF from a sequence of images.

        Args:
            images: List of PIL Images
            output_path: Output file path (.gif)
            duration: Duration per frame in milliseconds
        """
        if images:
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=0
            )
