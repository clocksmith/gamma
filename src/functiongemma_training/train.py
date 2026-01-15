"""
Minimal TRL training script for FunctionGemma.

Consumes a JSONL of experiences and trains a LoRA adapter.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TrainConfig:
    base_model: str = "google/gemma-2-2b-it"
    output_dir: str = "./functiongemma-adapter"
    max_seq_length: int = 512
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 1
    learning_rate: float = 2e-4
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05


def load_experiences(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def train(experiences_path: str, config: TrainConfig) -> str:
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from trl import SFTConfig, SFTTrainer
        from peft import LoraConfig, TaskType
        from datasets import Dataset
        import torch
    except ImportError as e:
        raise ImportError(
            f"Missing dependencies: {e}\n"
            "Install: pip install transformers trl peft datasets"
        )

    experiences = load_experiences(experiences_path)
    dataset = Dataset.from_list(experiences)

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        torch_dtype="auto",
        device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained(config.base_model)

    sft_config = SFTConfig(
        output_dir=config.output_dir,
        max_seq_length=config.max_seq_length,
        packing=False,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        lr_scheduler_type="constant",
        save_strategy="epoch",
        logging_steps=10,
        report_to="tensorboard",
        bf16=model.dtype == torch.bfloat16,
        fp16=model.dtype == torch.float16,
    )

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    trainer.train()

    output_path = Path(config.output_dir) / "adapter"
    trainer.save_model(str(output_path))
    return str(output_path)


def export_gguf(
    adapter_path: str,
    base_model: str,
    output_dir: str,
    quant: str = "Q4_K_M",
) -> None:
    """
    Print llama.cpp conversion commands for GGUF export.
    """
    print("\nGGUF export (llama.cpp):")
    print("1) Convert base model to GGUF:")
    print(f"   python convert-hf-to-gguf.py {base_model} --outtype f16 --outfile base.gguf")
    print("2) Merge LoRA adapter into GGUF:")
    print(f"   python convert-lora-to-gguf.py --base base.gguf --lora {adapter_path} --outfile merged.gguf")
    print("3) Quantize:")
    print(f"   ./quantize merged.gguf {Path(output_dir) / 'model.gguf'} {quant}")
    print("4) Import into Ollama:")
    print(f"   ollama create functiongemma-tuned -f Modelfile --from {Path(output_dir) / 'model.gguf'}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="FunctionGemma TRL trainer")
    parser.add_argument("experiences", help="Path to JSONL experiences")
    parser.add_argument("--base-model", default="google/gemma-2-2b-it")
    parser.add_argument("--output-dir", default="./functiongemma-adapter")
    parser.add_argument("--gguf", action="store_true", help="Print GGUF export commands")
    parser.add_argument("--gguf-quant", default="Q4_K_M", help="GGUF quantization")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-seq-length", type=int, default=512)
    args = parser.parse_args()

    cfg = TrainConfig(
        base_model=args.base_model,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        max_seq_length=args.max_seq_length,
    )

    path = train(args.experiences, cfg)
    print(f"Adapter saved to: {path}")
    if args.gguf:
        export_gguf(path, args.base_model, args.output_dir, quant=args.gguf_quant)
    else:
        print("For GGUF conversion, use llama.cpp's convert and quantize tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
