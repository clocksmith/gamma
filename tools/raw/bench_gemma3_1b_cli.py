import argparse
import gc
import time

# --- Configuration ---
PROMPT = "The quick brown fox jumps over the lazy dog."
NEW_TOKENS = 100
DEFAULT_MODEL_SPECS = {
    "google/gemma-3-1b-it": ["torch", "tf"],
    "google/gemma-3-1b-it-qat-q4_0-unquantized": ["torch", "tf"],
    "mlx-community/gemma-3-1b-it-4bit": ["mlx"],
    "mlx-community/gemma-3-1b-it-bf16": ["mlx"],
}
DEFAULT_MODELS = list(DEFAULT_MODEL_SPECS.keys())


def format_vram_stats(stats: dict) -> str:
    if not stats:
        return "n/a"
    parts = []
    for key, value in stats.items():
        if value is None:
            continue
        parts.append(f"{key}={value:.1f}MB")
    return " ".join(parts) if parts else "n/a"


def get_torch_vram_stats(device: str) -> dict:
    try:
        import torch
    except ImportError:
        return {}

    stats = {}
    if device == "cuda" and torch.cuda.is_available():
        stats["peak_mb"] = torch.cuda.max_memory_allocated() / (1024 * 1024)
    elif device == "mps" and torch.backends.mps.is_available():
        if hasattr(torch.mps, "current_allocated_memory"):
            stats["allocated_mb"] = torch.mps.current_allocated_memory() / (1024 * 1024)
        if hasattr(torch.mps, "driver_allocated_memory"):
            stats["driver_mb"] = torch.mps.driver_allocated_memory() / (1024 * 1024)
    return stats


def get_mlx_vram_stats() -> dict:
    try:
        import mlx.core as mx
    except ImportError:
        return {}

    stats = {}
    metal = getattr(mx, "metal", None)
    if metal:
        peak = getattr(metal, "get_peak_memory", None)
        active = getattr(metal, "get_active_memory", None)
        if callable(peak):
            stats["peak_mb"] = peak() / (1024 * 1024)
        if callable(active):
            stats["active_mb"] = active() / (1024 * 1024)
    return stats


def get_tf_vram_stats() -> dict:
    try:
        import tensorflow as tf
    except ImportError:
        return {}

    stats = {}
    try:
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            info = tf.config.experimental.get_memory_info('GPU:0')
            stats["current_mb"] = info.get("current", 0) / (1024 * 1024)
            if "peak" in info:
                stats["peak_mb"] = info.get("peak", 0) / (1024 * 1024)
    except Exception:
        return {}
    return stats


# --- Helper: Memory Cleanup ---
def cleanup(device_type="cpu"):
    """Aggressively clean memory to prevent interference between runs."""
    gc.collect()
    try:
        import torch
        if device_type == "mps" and torch.backends.mps.is_available():
            torch.mps.empty_cache()
    except ImportError:
        pass
    try:
        import tensorflow as tf
        tf.keras.backend.clear_session()
    except ImportError:
        pass


# --- Backend 1: PyTorch (Transformers) ---
def run_torch(model_id: str):
    print(f"\n--- [PyTorch/MPS] {model_id} ---")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        return "Skipped (torch/transformers not installed)", 0.0, {}

    cleanup("mps")
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    print(f"   Backend: {device.upper()}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    print("   Loading model...")
    t0 = time.time()
    try:
        # Force float16 to avoid BFloat16 embedding crashes on Mac
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map=device,
            trust_remote_code=True,
        )
    except Exception as e:
        return f"Load Failed: {e}", 0.0, {}
    load_time = time.time() - t0
    print(f"   Loaded in {load_time:.2f}s")

    # Inputs: Force Long type for MPS stability
    inputs = tokenizer(PROMPT, return_tensors="pt")
    input_ids = inputs["input_ids"].to(device=device, dtype=torch.long)
    attention_mask = inputs["attention_mask"].to(device=device, dtype=torch.long)

    model.eval()

    print("   Warming up...")
    with torch.no_grad():
        _ = model.generate(input_ids=input_ids, attention_mask=attention_mask, max_new_tokens=10, do_sample=False)
    if device == "mps":
        torch.mps.synchronize()

    print(f"   Generating {NEW_TOKENS} tokens...")
    t0 = time.time()
    with torch.no_grad():
        _ = model.generate(input_ids=input_ids, attention_mask=attention_mask, max_new_tokens=NEW_TOKENS, do_sample=False)
    if device == "mps":
        torch.mps.synchronize()
    total_time = time.time() - t0

    vram_stats = get_torch_vram_stats(device)
    print(f"   VRAM: {format_vram_stats(vram_stats)}")
    return NEW_TOKENS / total_time, load_time, vram_stats


# --- Backend 2: MLX (Apple Silicon Native) ---
def run_mlx(model_id: str):
    print(f"\n--- [MLX] {model_id} ---")
    try:
        from mlx_lm import load, generate
    except ImportError:
        return "Skipped (mlx-lm not installed)", 0.0, {}

    cleanup()

    print("   Loading model...")
    t0 = time.time()
    try:
        model, tokenizer = load(model_id)
    except Exception as e:
        return f"Load Failed (Is this an MLX model?): {e}", 0.0, {}
    load_time = time.time() - t0
    print(f"   Loaded in {load_time:.2f}s")

    print("   Warming up...")
    generate(model, tokenizer, prompt=PROMPT, max_tokens=10, verbose=False)

    print(f"   Generating {NEW_TOKENS} tokens...")
    t0 = time.time()
    _ = generate(model, tokenizer, prompt=PROMPT, max_tokens=NEW_TOKENS, verbose=False)
    total_time = time.time() - t0

    vram_stats = get_mlx_vram_stats()
    print(f"   VRAM: {format_vram_stats(vram_stats)}")
    return NEW_TOKENS / total_time, load_time, vram_stats


# --- Backend 3: TensorFlow (Transformers) ---
def run_tensorflow(model_id: str):
    print(f"\n--- [TensorFlow] {model_id} ---")
    try:
        import tensorflow as tf
        from transformers import TFAutoModelForCausalLM, AutoTokenizer
    except ImportError:
        return "Skipped (tensorflow/transformers not installed)", 0.0, {}

    cleanup()

    # Check for GPU/Metal
    gpus = tf.config.list_physical_devices('GPU')
    print(f"   Backend: {'Metal/GPU' if gpus else 'CPU'}")

    tokenizer = AutoTokenizer.from_pretrained(model_id)

    print("   Loading model...")
    t0 = time.time()
    try:
        # Try loading native TF weights first, fallback to PT conversion if needed
        try:
            model = TFAutoModelForCausalLM.from_pretrained(model_id)
        except OSError:
            print("   (Native TF weights missing, attempting on-the-fly conversion from PyTorch...)")
            model = TFAutoModelForCausalLM.from_pretrained(model_id, from_pt=True)
    except Exception as e:
        return f"Load Failed: {e}", 0.0, {}
    load_time = time.time() - t0
    print(f"   Loaded in {load_time:.2f}s")

    print("   Warming up (XLA compiling)...")
    inputs = tokenizer(PROMPT, return_tensors="tf")
    _ = model.generate(**inputs, max_new_tokens=4, do_sample=False)

    print(f"   Generating {NEW_TOKENS} tokens...")
    t0 = time.time()
    _ = model.generate(**inputs, max_new_tokens=NEW_TOKENS, do_sample=False)
    total_time = time.time() - t0

    vram_stats = get_tf_vram_stats()
    print(f"   VRAM: {format_vram_stats(vram_stats)}")
    return NEW_TOKENS / total_time, load_time, vram_stats


# --- Backend 4: Llama.cpp (GGUF) ---
def run_gguf(model_path: str):
    print(f"\n--- [Llama.cpp] {model_path} ---")
    try:
        from llama_cpp import Llama
    except ImportError:
        return "Skipped (llama-cpp-python not installed)", 0.0, {}

    cleanup()

    print("   Loading model...")
    t0 = time.time()
    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=1024,
            n_gpu_layers=-1, # Offload all to GPU/Metal
            verbose=False
        )
    except Exception as e:
        return f"Load Failed: {e}", 0.0, {}
    load_time = time.time() - t0
    print(f"   Loaded in {load_time:.2f}s")

    print("   Warming up...")
    llm(PROMPT, max_tokens=5)

    print(f"   Generating {NEW_TOKENS} tokens...")
    t0 = time.time()
    llm(PROMPT, max_tokens=NEW_TOKENS)
    total_time = time.time() - t0

    return NEW_TOKENS / total_time, load_time, {}


def main():
    parser = argparse.ArgumentParser(description="Universal Mac LLM Benchmark")
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS, help="Model IDs or Paths")
    parser.add_argument("--run-torch", action=argparse.BooleanOptionalAction, default=True, help="Run PyTorch backend")
    parser.add_argument("--run-mlx", action=argparse.BooleanOptionalAction, default=True, help="Run MLX backend")
    parser.add_argument("--run-tf", action=argparse.BooleanOptionalAction, default=True, help="Run TensorFlow backend (Experimental)")
    parser.add_argument("--run-gguf", action=argparse.BooleanOptionalAction, default=False, help="Run GGUF backend (Requires path to .gguf file)")
    args = parser.parse_args()

    results = []

    for model_id in args.models:
        backends = DEFAULT_MODEL_SPECS.get(model_id)
        if not backends:
            if model_id.lower().endswith(".gguf"):
                backends = ["gguf"]
            elif "mlx" in model_id.lower():
                backends = ["mlx"]
            else:
                backends = ["torch", "tf"]

        for backend in backends:
            if backend == "mlx" and args.run_mlx:
                tps, load_t, vram = run_mlx(model_id)
                results.append((model_id, "MLX", tps, load_t, vram))
            elif backend == "gguf" and args.run_gguf:
                tps, load_t, vram = run_gguf(model_id)
                results.append((model_id, "Llama.cpp", tps, load_t, vram))
            elif backend == "torch" and args.run_torch:
                tps, load_t, vram = run_torch(model_id)
                results.append((model_id, "PyTorch", tps, load_t, vram))
            elif backend == "tf" and args.run_tf:
                tps, load_t, vram = run_tensorflow(model_id)
                results.append((model_id, "TensorFlow", tps, load_t, vram))

    # --- Report ---
    print("\n" + "=" * 90)
    print(f"{'Model / Engine':<40} | {'Load(s)':<8} | {'Tok/s':<8} | {'VRAM':<20}")
    print("-" * 90)
    for res in results:
        model_name = res[0].split("/")[-1][:25]
        engine = res[1]
        tps = res[2]
        load_t = res[3]
        vram_stats = res[4]

        if isinstance(tps, str):  # Error message
            print(f"{model_name:<25} ({engine}) | {'ERROR':<8} | {tps} | {'n/a':<20}")
        else:
            vram_str = format_vram_stats(vram_stats)
            print(f"{model_name:<25} ({engine}) | {load_t:<8.2f} | {tps:<8.2f} | {vram_str:<20}")
    print("=" * 90)


if __name__ == "__main__":
    main()
