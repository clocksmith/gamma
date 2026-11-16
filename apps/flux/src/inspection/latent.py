"""
Latent space visualization tools.

Visualize VAE latent representations during the diffusion process.
"""

from typing import List, Optional
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.cm as cm


class LatentVisualizer:
    """
    Visualize latent space representations.

    Provides educational visualizations of the VAE latent space
    during diffusion denoising.
    """

    @staticmethod
    def visualize_latent_channels(
        latent: np.ndarray,
        title: Optional[str] = None
    ) -> Image.Image:
        """
        Visualize all channels of a latent tensor.

        Args:
            latent: Latent array (batch, channels, height, width)
            title: Optional title for the visualization

        Returns:
            PIL Image showing all channels
        """
        if latent.ndim == 4:
            latent = latent[0]  # Take first batch

        c, h, w = latent.shape

        # Create grid
        cols = min(c, 4)
        rows = (c + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3))

        if rows == 1 and cols == 1:
            axes = [[axes]]
        elif rows == 1:
            axes = [axes]
        elif cols == 1:
            axes = [[ax] for ax in axes]

        for i in range(rows):
            for j in range(cols):
                idx = i * cols + j

                if idx < c:
                    # Show channel
                    channel = latent[idx]

                    # Normalize for visualization
                    channel = (channel - channel.min()) / (channel.max() - channel.min() + 1e-8)

                    axes[i][j].imshow(channel, cmap='viridis')
                    axes[i][j].set_title(f"Channel {idx}")
                    axes[i][j].axis('off')
                else:
                    # Hide unused subplots
                    axes[i][j].axis('off')

        if title:
            fig.suptitle(title, fontsize=16)

        plt.tight_layout()

        # Convert to PIL Image
        fig.canvas.draw()
        img_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img_array = img_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))

        plt.close(fig)

        return Image.fromarray(img_array)

    @staticmethod
    def visualize_latent_statistics(
        latents: List[np.ndarray],
        step_indices: List[int]
    ) -> Image.Image:
        """
        Visualize statistics of latents over denoising steps.

        Args:
            latents: List of latent arrays at different steps
            step_indices: List of step indices

        Returns:
            PIL Image showing statistics plot
        """
        # Compute statistics
        means = [lat.mean() for lat in latents]
        stds = [lat.std() for lat in latents]
        mins = [lat.min() for lat in latents]
        maxs = [lat.max() for lat in latents]

        # Create plot
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Mean
        axes[0, 0].plot(step_indices, means, 'b-', linewidth=2)
        axes[0, 0].set_title("Mean Value")
        axes[0, 0].set_xlabel("Step")
        axes[0, 0].set_ylabel("Mean")
        axes[0, 0].grid(True, alpha=0.3)

        # Standard deviation
        axes[0, 1].plot(step_indices, stds, 'r-', linewidth=2)
        axes[0, 1].set_title("Standard Deviation (Noise Level)")
        axes[0, 1].set_xlabel("Step")
        axes[0, 1].set_ylabel("Std Dev")
        axes[0, 1].grid(True, alpha=0.3)

        # Min/Max range
        axes[1, 0].fill_between(step_indices, mins, maxs, alpha=0.3, color='green')
        axes[1, 0].plot(step_indices, mins, 'g--', label='Min')
        axes[1, 0].plot(step_indices, maxs, 'g-', label='Max')
        axes[1, 0].set_title("Value Range")
        axes[1, 0].set_xlabel("Step")
        axes[1, 0].set_ylabel("Value")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Distribution evolution (histogram of final step)
        if latents:
            final_latent = latents[-1].flatten()
            axes[1, 1].hist(final_latent, bins=50, alpha=0.7, color='purple', edgecolor='black')
            axes[1, 1].set_title("Final Latent Distribution")
            axes[1, 1].set_xlabel("Value")
            axes[1, 1].set_ylabel("Frequency")
            axes[1, 1].grid(True, alpha=0.3, axis='y')

        plt.suptitle("Latent Space Evolution", fontsize=16)
        plt.tight_layout()

        # Convert to PIL Image
        fig.canvas.draw()
        img_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img_array = img_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))

        plt.close(fig)

        return Image.fromarray(img_array)

    @staticmethod
    def create_latent_evolution_animation(
        latents: List[np.ndarray],
        output_path: str,
        channel: int = 0,
        duration: int = 200
    ):
        """
        Create an animated GIF showing latent evolution.

        Args:
            latents: List of latent arrays at different steps
            output_path: Output file path (.gif)
            channel: Which channel to visualize
            duration: Duration per frame in milliseconds
        """
        frames = []

        for i, latent in enumerate(latents):
            if latent.ndim == 4:
                latent = latent[0]  # Take first batch

            # Extract channel
            channel_data = latent[channel]

            # Normalize
            channel_data = (channel_data - channel_data.min()) / (channel_data.max() - channel_data.min() + 1e-8)

            # Convert to image
            channel_uint8 = (channel_data * 255).astype(np.uint8)
            frame = Image.fromarray(channel_uint8, mode='L')

            # Resize for better visibility
            frame = frame.resize((256, 256), Image.NEAREST)

            frames.append(frame)

        # Save as GIF
        if frames:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration,
                loop=0
            )

    @staticmethod
    def compare_latents(
        latent1: np.ndarray,
        latent2: np.ndarray,
        label1: str = "Latent 1",
        label2: str = "Latent 2"
    ) -> Image.Image:
        """
        Compare two latent representations.

        Args:
            latent1: First latent array
            latent2: Second latent array
            label1: Label for first latent
            label2: Label for second latent

        Returns:
            PIL Image showing comparison
        """
        if latent1.ndim == 4:
            latent1 = latent1[0]
        if latent2.ndim == 4:
            latent2 = latent2[0]

        # Compute difference
        diff = np.abs(latent1 - latent2)

        # Visualize first channel of each
        c1 = latent1[0]
        c2 = latent2[0]
        d = diff[0]

        # Normalize
        c1 = (c1 - c1.min()) / (c1.max() - c1.min() + 1e-8)
        c2 = (c2 - c2.min()) / (c2.max() - c2.min() + 1e-8)
        d = (d - d.min()) / (d.max() - d.min() + 1e-8)

        # Create plot
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        axes[0].imshow(c1, cmap='viridis')
        axes[0].set_title(label1)
        axes[0].axis('off')

        axes[1].imshow(c2, cmap='viridis')
        axes[1].set_title(label2)
        axes[1].axis('off')

        axes[2].imshow(d, cmap='hot')
        axes[2].set_title("Absolute Difference")
        axes[2].axis('off')

        plt.tight_layout()

        # Convert to PIL Image
        fig.canvas.draw()
        img_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img_array = img_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))

        plt.close(fig)

        return Image.fromarray(img_array)
