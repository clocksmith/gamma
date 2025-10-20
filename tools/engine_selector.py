#!/usr/bin/env python3
"""
Engine Selector - Interactive tool to help choose the right engine for your model and use case.
"""

import sys
import os
import platform

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.model_validator import ModelValidator


def detect_hardware():
    """Detect available hardware."""
    hw_info = {
        'platform': platform.system(),
        'machine': platform.machine(),
        'cuda': False,
        'mps': False,
        'cpu_only': True
    }

    # Check CUDA
    try:
        import torch
        if torch.cuda.is_available():
            hw_info['cuda'] = True
            hw_info['cpu_only'] = False
            hw_info['cuda_device'] = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    # Check Apple Silicon MPS
    try:
        import torch
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            hw_info['mps'] = True
            hw_info['cpu_only'] = False
    except ImportError:
        pass

    return hw_info


def print_hardware_info(hw_info):
    """Print detected hardware information."""
    print("\n" + "="*70)
    print("Detected Hardware")
    print("="*70)
    print(f"Platform: {hw_info['platform']} ({hw_info['machine']})")

    if hw_info['cuda']:
        print(f"✓ CUDA Available: {hw_info.get('cuda_device', 'Yes')}")
    else:
        print("✗ CUDA Not Available")

    if hw_info['mps']:
        print("✓ Apple Metal (MPS) Available")
    else:
        print("✗ Apple Metal Not Available")

    if hw_info['cpu_only']:
        print("\n⚠️  Running on CPU only")

    print("="*70)


def recommend_engines_for_use_case(use_case, hw_info):
    """Recommend engines based on use case and hardware."""
    recommendations = {}

    if use_case == 'speed':
        if hw_info['cuda']:
            recommendations = {
                'primary': 'vllm',
                'alternative': ['pytorch_cuda', 'llamacpp'],
                'reason': 'vLLM provides fastest inference on NVIDIA GPUs with PagedAttention'
            }
        elif hw_info['mps']:
            recommendations = {
                'primary': 'mlx_gpu',
                'alternative': ['llamacpp', 'mlx', 'pytorch'],
                'reason': 'MLX GPU is optimized for Apple Silicon with Metal acceleration'
            }
        else:
            recommendations = {
                'primary': 'llamacpp',
                'alternative': ['onnx', 'pytorch'],
                'reason': 'llamacpp with quantized GGUF files provides best CPU performance'
            }

    elif use_case == 'mind_meld':
        if hw_info['cuda']:
            recommendations = {
                'primary': 'pytorch_cuda',
                'alternative': ['vllm', 'pytorch'],
                'reason': 'PyTorch CUDA provides full logits access with good CUDA performance',
                'warning': '⚠️  Do NOT use ollama engine - it has no logits access!'
            }
        elif hw_info['mps']:
            recommendations = {
                'primary': 'mlx_gpu',
                'alternative': ['pytorch', 'mlx'],
                'reason': 'MLX GPU provides full logits with Apple Silicon optimization',
                'warning': '⚠️  Do NOT use ollama engine - it has no logits access!'
            }
        else:
            recommendations = {
                'primary': 'pytorch',
                'alternative': ['llamacpp'],
                'reason': 'PyTorch provides full logits access for mind melding',
                'warning': '⚠️  Do NOT use ollama engine - it has no logits access!'
            }

    elif use_case == 'research':
        recommendations = {
            'primary': 'pytorch',
            'alternative': ['jax'],
            'reason': 'PyTorch provides best flexibility, debugging, and research tools'
        }

    elif use_case == 'production':
        if hw_info['cuda']:
            recommendations = {
                'primary': 'vllm',
                'alternative': ['pytorch_cuda'],
                'reason': 'vLLM optimized for production throughput with batch processing'
            }
        elif hw_info['mps']:
            recommendations = {
                'primary': 'mlx_gpu',
                'alternative': ['llamacpp'],
                'reason': 'MLX GPU provides stable production performance on Apple Silicon'
            }
        else:
            recommendations = {
                'primary': 'llamacpp',
                'alternative': ['onnx'],
                'reason': 'llamacpp provides stable, efficient CPU inference for production'
            }

    return recommendations


def recommend_for_model(model_identifier):
    """Recommend engine for a specific model."""
    print(f"\n🔍 Analyzing model: {model_identifier}")

    model_format = ModelValidator.detect_model_format(model_identifier)
    print(f"Detected format: {model_format}")

    suggestions = ModelValidator.suggest_engine_for_model(model_identifier)

    print(f"\n✅ Recommended engines:")
    for i, engine in enumerate(suggestions, 1):
        if i == 1:
            print(f"  {i}. {engine} (BEST)")
        else:
            print(f"  {i}. {engine}")

    # Provide usage examples
    print(f"\n📝 Usage examples:")
    for engine in suggestions[:2]:  # Show top 2
        print(f"\n  # {engine.upper()}")
        print(f"  python tools/benchmark_model_speed.py \\")
        print(f"    --models {engine}:{model_identifier}")


def interactive_mode():
    """Interactive engine selector."""
    print("\n" + "="*70)
    print("🎯 GAMMA Engine Selector")
    print("="*70)
    print("Help choose the right engine for your model and use case\n")

    # Detect hardware
    hw_info = detect_hardware()
    print_hardware_info(hw_info)

    # Ask for mode
    print("\nWhat would you like to do?")
    print("  1. Get engine recommendation for a specific model")
    print("  2. Get engine recommendation for a use case")
    print("  3. Validate a model specification")
    print("  4. Exit")

    choice = input("\nYour choice (1-4): ").strip()

    if choice == '1':
        # Model-specific recommendation
        print("\n" + "-"*70)
        print("Enter your model identifier:")
        print("  Examples:")
        print("    - google/gemma-2-2b-it (HuggingFace)")
        print("    - ./models/llama-2-7b-q4.gguf (local GGUF)")
        print("    - llama2 (Ollama)")
        print("    - ./models/model.onnx (ONNX)")

        model = input("\nModel: ").strip()
        if model:
            recommend_for_model(model)

    elif choice == '2':
        # Use case recommendation
        print("\n" + "-"*70)
        print("What's your primary use case?")
        print("  1. Speed (fastest inference)")
        print("  2. Mind melding (requires logits)")
        print("  3. Research/experimentation")
        print("  4. Production deployment")

        use_case_choice = input("\nUse case (1-4): ").strip()

        use_case_map = {
            '1': 'speed',
            '2': 'mind_meld',
            '3': 'research',
            '4': 'production'
        }

        use_case = use_case_map.get(use_case_choice)

        if use_case:
            recommendations = recommend_engines_for_use_case(use_case, hw_info)

            print(f"\n✅ Recommendation for {use_case.replace('_', ' ').title()}:")
            print(f"\n  Primary: {recommendations['primary']}")
            print(f"  Reason: {recommendations['reason']}")

            if 'alternative' in recommendations:
                print(f"\n  Alternatives: {', '.join(recommendations['alternative'])}")

            if 'warning' in recommendations:
                print(f"\n  {recommendations['warning']}")

            # Show example command
            print(f"\n📝 Example command:")
            if use_case == 'mind_meld':
                print(f"  python tools/run_mind_meld_cli.py \\")
                print(f"    --models {recommendations['primary']}:google/gemma-2-2b-it \\")
                print(f"             {recommendations['primary']}:Qwen/Qwen2-7B-Instruct \\")
                print(f"    --strategy pattern --steps 30")
            else:
                print(f"  python tools/benchmark_model_speed.py \\")
                print(f"    --models {recommendations['primary']}:google/gemma-2-2b-it")

    elif choice == '3':
        # Validation
        print("\n" + "-"*70)
        print("Enter model specification to validate (format: engine:model):")
        print("  Examples:")
        print("    - pytorch:google/gemma-2-2b-it")
        print("    - llamacpp:./models/model.gguf")
        print("    - ollama:llama2")

        spec = input("\nSpecification: ").strip()

        if spec:
            require_logits_input = input("Require logits access (for mind melding)? (y/n) [n]: ").strip().lower()
            require_logits = require_logits_input == 'y'

            validation_result = ModelValidator.validate_model_spec(spec, require_logits)

            if validation_result.is_valid:
                print(f"\n✅ Valid configuration!")
                if validation_result.warning_message:
                    print(f"\n{validation_result.warning_message}")
                    if validation_result.suggestion:
                        print(f"💡 {validation_result.suggestion}")
            else:
                print(f"\n❌ Invalid configuration")
                print(f"   {validation_result.error_message}")
                if validation_result.suggestion:
                    print(f"💡 Suggestion: {validation_result.suggestion}")

    elif choice == '4':
        print("\nExiting...")
        return

    else:
        print("\n❌ Invalid choice")

    # Ask to continue
    print("\n" + "-"*70)
    cont = input("\nRun selector again? (y/n): ").strip().lower()
    if cont == 'y':
        interactive_mode()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Non-interactive mode with model argument
        model = sys.argv[1]
        hw_info = detect_hardware()
        print_hardware_info(hw_info)
        recommend_for_model(model)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
