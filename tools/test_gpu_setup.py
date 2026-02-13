#!/usr/bin/env python3
"""
GPU Setup Testing Tool
Tests GPU detection, driver versions, and compute capabilities
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.hardware.gpu_discovery import get_gpu_info, format_gpu_info


def test_pytorch():
    """Test PyTorch GPU support."""
    print("\n" + "="*70)
    print("PyTorch GPU Detection")
    print("="*70)

    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")

        # Check CUDA
        cuda_available = torch.cuda.is_available()
        print(f"  CUDA available: {cuda_available}")

        if cuda_available:
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  Device count: {torch.cuda.device_count()}")

            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"\n  GPU {i}: {props.name}")
                print(f"    Total memory: {props.total_memory / (1024**3):.2f} GB")
                print(f"    Compute capability: {props.major}.{props.minor}")

        # Check ROCm
        hip_version = getattr(torch.version, "hip", None)
        if hip_version:
            print(f"  ROCm/HIP version: {hip_version}")
            if cuda_available:
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    if hasattr(props, 'gcnArchName'):
                        print(f"    GPU {i} GCN Architecture: {props.gcnArchName}")

        # Test tensor creation
        print("\n  Testing tensor creation...")
        if cuda_available:
            device = torch.device('cuda:0')
            x = torch.randn(100, 100, device=device)
            y = torch.randn(100, 100, device=device)
            z = torch.mm(x, y)
            print(f"  ✓ Successfully created and multiplied tensors on GPU")
            print(f"    Result shape: {z.shape}")
        else:
            print(f"  ⚠ No GPU available, using CPU")
            x = torch.randn(100, 100)
            y = torch.randn(100, 100)
            z = torch.mm(x, y)
            print(f"  ✓ Successfully created and multiplied tensors on CPU")

        return True

    except ImportError as e:
        print(f"✗ PyTorch not installed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing PyTorch: {e}")
        return False


def test_triton():
    """Test Triton support."""
    print("\n" + "="*70)
    print("Triton GPU Detection")
    print("="*70)

    try:
        import triton
        print(f"✓ Triton version: {triton.__version__}")

        # Check if CUDA/ROCm is available for Triton
        try:
            import torch
            if torch.cuda.is_available():
                print(f"  ✓ Triton can use GPU acceleration")

                # Check for ROCm-specific Triton features
                hip_version = getattr(torch.version, "hip", None)
                if hip_version:
                    print(f"  ✓ Triton ROCm support enabled (HIP {hip_version})")
            else:
                print(f"  ⚠ Triton installed but no GPU available")
        except ImportError:
            print(f"  ⚠ PyTorch not available, can't check GPU support")

        return True

    except ImportError:
        print(f"✗ Triton not installed")
        return False
    except Exception as e:
        print(f"✗ Error testing Triton: {e}")
        return False


def test_vllm():
    """Test vLLM support."""
    print("\n" + "="*70)
    print("vLLM GPU Detection")
    print("="*70)

    try:
        import vllm
        print(f"✓ vLLM version: {vllm.__version__}")

        # Check GPU requirements
        try:
            import torch
            if torch.cuda.is_available():
                print(f"  ✓ vLLM can use GPU acceleration")

                # Check memory requirements
                props = torch.cuda.get_device_properties(0)
                vram_gb = props.total_memory / (1024**3)
                print(f"  GPU VRAM: {vram_gb:.2f} GB")

                if vram_gb < 8:
                    print(f"  ⚠ Warning: vLLM typically requires 8+ GB VRAM")
                    print(f"    Consider using smaller quantized models")
                else:
                    print(f"  ✓ Sufficient VRAM for most models")
            else:
                print(f"  ⚠ vLLM installed but no GPU available")
                print(f"    vLLM performance will be significantly slower on CPU")
        except ImportError:
            print(f"  ⚠ PyTorch not available, can't check GPU support")

        return True

    except ImportError:
        print(f"✗ vLLM not installed")
        return False
    except Exception as e:
        print(f"✗ Error testing vLLM: {e}")
        return False


def test_llama_cpp():
    """Test llama-cpp-python GPU offload support."""
    print("\n" + "="*70)
    print("llama.cpp Backend Detection")
    print("="*70)

    try:
        from llama_cpp import llama_supports_gpu_offload
        supports_gpu = bool(llama_supports_gpu_offload())
        print(f"  GPU offload support: {supports_gpu}")
        if supports_gpu:
            print("  ✓ llama-cpp-python was built with a GPU backend")
        else:
            print("  ⚠ llama-cpp-python is CPU-only (or GPU backend unavailable)")
            print("    Rebuild with Vulkan/CUDA/Metal backend flags if needed")
        return supports_gpu
    except ImportError:
        print("✗ llama-cpp-python not installed")
        return False
    except Exception as e:
        print(f"✗ Error testing llama-cpp-python: {e}")
        return False


def test_system_gpu():
    """Test system-level GPU detection."""
    print("\n" + "="*70)
    print("System GPU Detection (lspci)")
    print("="*70)

    try:
        import subprocess
        result = subprocess.run(
            ['lspci'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # Filter for VGA/Display/3D controllers
            gpu_lines = [line for line in result.stdout.split('\n')
                        if any(keyword in line.lower()
                              for keyword in ['vga', 'display', '3d'])]

            if gpu_lines:
                print("  Detected GPUs:")
                for line in gpu_lines:
                    print(f"    {line}")
            else:
                print("  ⚠ No GPUs detected via lspci")
        else:
            print(f"  ✗ lspci command failed")

        return len(gpu_lines) > 0 if 'gpu_lines' in locals() else False

    except FileNotFoundError:
        print(f"  ✗ lspci command not found")
        return False
    except Exception as e:
        print(f"  ✗ Error running lspci: {e}")
        return False


def test_gpu_discovery():
    """Test our GPU discovery module."""
    print("\n" + "="*70)
    print("Gamma GPU Discovery Module")
    print("="*70)

    try:
        gpus = get_gpu_info()

        if gpus:
            print(format_gpu_info(gpus))

            # Additional details
            for gpu in gpus:
                if gpu.library != 'cpu':
                    print(f"\n  GPU {gpu.id} Details:")
                    print(f"    Library: {gpu.library}")
                    print(f"    Compute: {gpu.compute_capability}")
                    print(f"    VRAM: {gpu.vram_total_mb / 1024:.2f} GB")
        else:
            print("  ⚠ No GPUs detected by discovery module")

        return len([g for g in gpus if g.library != 'cpu']) > 0

    except Exception as e:
        print(f"  ✗ Error in GPU discovery: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "="*70)
    print("GPU Setup Summary")
    print("="*70)

    total = len(results)
    passed = sum(results.values())

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} {test_name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 All GPU tests passed!")
        print("  Your system is ready for GPU-accelerated inference.")
    elif passed > 0:
        print("\n  ⚠ Some GPU tests passed, but not all.")
        print("  You may have partial GPU support.")
    else:
        print("\n  ✗ No GPU support detected.")
        print("  Install mesa-utils and vulkan-tools:")
        print("    sudo apt install mesa-utils vulkan-tools")


def main():
    """Run all GPU tests."""
    print("🔍 GPU Setup Testing Tool")
    print("Testing GPU detection and compute capabilities...")

    results = {
        "System GPU Detection": test_system_gpu(),
        "GPU Discovery Module": test_gpu_discovery(),
        "PyTorch GPU Support": test_pytorch(),
        "llama.cpp GPU Support": test_llama_cpp(),
        "Triton Support": test_triton(),
        "vLLM Support": test_vllm(),
    }

    print_summary(results)

    # Exit code: 0 if all passed, 1 otherwise
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
