"""Setup script for Flux."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flux-diffusion",
    version="0.1.0",
    author="Flux Team",
    description="Interactive diffusion model learning lab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.10",
    install_requires=[
        "gamma-core>=0.1.0",
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
        "transformers>=4.35.0",
        "torch>=2.1.0",
    ],
    extras_require={
        "pytorch": [
            "diffusers>=0.25.0",
            "accelerate>=0.25.0",
            "safetensors>=0.4.0",
        ],
        "mlx": [
            "mlx>=0.5.0",
            "mlx-stable-diffusion>=0.1.0",
        ],
        "all": [
            "diffusers>=0.25.0",
            "accelerate>=0.25.0",
            "safetensors>=0.4.0",
            "mlx>=0.5.0",
            "mlx-stable-diffusion>=0.1.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flux=flux:main",
        ],
    },
)
