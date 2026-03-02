#!/usr/bin/env python3
"""
Mind Meld CLI - Standalone interface for Mind Meld mode

Supports multiple configuration methods:
- YAML config files: mind-meld config.yaml
- Presets: mind-meld --preset creative
- Model aliases: mind-meld gemma-1b gemma-2b
- Persona binding: mind-meld gemma-1b@Optimist gemma-2b@Skeptic
- Simplified blend: mind-meld --blend dynamic
- CLI flags that override config values
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add project root to the path to allow importing from src
try:
    from tools._path_setup import ensure_project_root_on_path
except ImportError:
    from _path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from src.core.engine_interface import LLMEngine
from src.ui import displays as ui
from src.core import config as cfg
from src.mind_meld.mode import MindMeldMode
from src.mind_meld.core.config import SwapStrategy
from src.mind_meld.cli.config import (
    MindMeldCLIConfig,
    ModelSpec,
    BlendConfig,
    resolve_config,
    PRESETS_DIR,
)
from src.engines.engine_factory import get_engine
from src.core.model_validator import ModelValidator, print_validation_result


class MindMeldCLI:
    """Mind Meld CLI with YAML config support."""

    STRATEGY_MAP = {
        "pattern": SwapStrategy.PATTERN_BASED,
        "pattern_based": SwapStrategy.PATTERN_BASED,
        "fixed": SwapStrategy.FIXED_INTERVAL,
        "fixed_interval": SwapStrategy.FIXED_INTERVAL,
        "round_robin": SwapStrategy.ROUND_ROBIN,
        "random": SwapStrategy.RANDOM,
        "confidence": SwapStrategy.CONFIDENCE_BASED,
        "confidence_based": SwapStrategy.CONFIDENCE_BASED,
        "perplexity": SwapStrategy.PERPLEXITY_BASED,
        "perplexity_based": SwapStrategy.PERPLEXITY_BASED,
        "attention": SwapStrategy.ATTENTION_GUIDED,
        "attention_guided": SwapStrategy.ATTENTION_GUIDED,
        "weighted": SwapStrategy.WEIGHTED_BLEND,
        "weighted_blend": SwapStrategy.WEIGHTED_BLEND,
        "semantic": SwapStrategy.SEMANTIC_SIMILARITY,
        "semantic_similarity": SwapStrategy.SEMANTIC_SIMILARITY,
    }

    BLEND_MODES = ["hard", "soft", "dynamic", "smooth"]

    def __init__(self):
        self.config: Optional[MindMeldCLIConfig] = None

    def parse_args(self) -> argparse.Namespace:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(
            description="Mind Meld CLI - meld multiple LLMs together",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_epilog(),
        )

        # Positional: either config file or model specs
        parser.add_argument(
            "models_or_config",
            nargs="*",
            metavar="MODEL_OR_CONFIG",
            help="Model specs (engine:model or alias), or path to YAML config file",
        )

        # Config options
        config_group = parser.add_argument_group("Configuration")
        config_group.add_argument(
            "--preset", "-p",
            type=str,
            choices=self._list_presets(),
            help="Load a preset configuration",
        )
        config_group.add_argument(
            "--config", "-c",
            type=str,
            metavar="FILE",
            help="Load configuration from YAML file",
        )
        config_group.add_argument(
            "--save-config",
            type=str,
            metavar="FILE",
            help="Save final configuration to YAML file and exit",
        )

        # Model options
        model_group = parser.add_argument_group("Models")
        model_group.add_argument(
            "--models", "-m",
            type=str,
            nargs="+",
            metavar="SPEC",
            help="Model specs: engine:model, alias, or model@persona",
        )

        # Blend options (simplified)
        blend_group = parser.add_argument_group("Blending")
        blend_group.add_argument(
            "--blend", "-b",
            type=str,
            metavar="MODE_OR_STRENGTH",
            help="Blend mode (hard/soft/dynamic/smooth) or strength (0-100)",
        )
        blend_group.add_argument(
            "--blend-strategy",
            type=str,
            choices=[
                "weighted_average", "confidence_weighted", "dynamic_weighted",
                "attention_weighted", "learned", "hierarchical", "ensemble_voting"
            ],
            help="Detailed blending strategy",
        )

        # Strategy options
        strategy_group = parser.add_argument_group("Swap Strategy")
        strategy_group.add_argument(
            "--strategy", "-s",
            type=str,
            choices=list(self.STRATEGY_MAP.keys()),
            help="Model swap strategy",
        )
        strategy_group.add_argument(
            "--interval", "-i",
            type=int,
            help="Token interval for fixed swap strategy",
        )

        # Generation options
        gen_group = parser.add_argument_group("Generation")
        gen_group.add_argument("--prompt", type=str, help="Initial prompt")
        gen_group.add_argument("--steps", "-n", type=int, help="Number of generation steps")
        gen_group.add_argument("--temperature", "-t", type=float, help="Generation temperature")
        gen_group.add_argument("--top-k", type=int, help="Top-K sampling")
        gen_group.add_argument("--top-p", type=float, help="Top-P (nucleus) sampling")
        gen_group.add_argument("--repetition-penalty", type=float, help="Repetition penalty")
        gen_group.add_argument("--max-sentences", type=int, help="Stop after N sentences")
        gen_group.add_argument("--stop-text", action="append", default=[], help="Stop on text (repeatable)")

        # Persona options
        persona_group = parser.add_argument_group("Personas")
        persona_group.add_argument(
            "--persona",
            action="append",
            dest="personas",
            metavar="TEXT",
            help="Per-model persona/system prompt (repeat for each model)",
        )
        persona_group.add_argument(
            "--prompt-system",
            type=str,
            help="Global system prompt",
        )
        persona_group.add_argument(
            "--prompt-chat-template",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Use chat template for prompt formatting",
        )
        persona_group.add_argument(
            "--no-default-system",
            action="store_true",
            help="Disable default system prompt",
        )

        # Output options
        output_group = parser.add_argument_group("Output")
        output_group.add_argument(
            "--output", "-o",
            type=str,
            choices=["terminal", "json", "markdown"],
            help="Output format",
        )
        output_group.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        output_group.add_argument("--summary-only", action="store_true", help="Show only final summary")
        output_group.add_argument("--headless", action="store_true", help="Run without interactive output")
        output_group.add_argument("--no-step-delay", action="store_true", help="Disable step delay")
        output_group.add_argument(
            "--show-attention",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Toggle attention display",
        )
        output_group.add_argument("--stats-file", type=str, help="Save stats to JSON file")
        output_group.add_argument("--meld-diagnostics", action="store_true", help="Show meld diagnostics")

        # Advanced options
        adv_group = parser.add_argument_group("Advanced")
        adv_group.add_argument("--translate-logits", action="store_true", help="Enable logit translation")
        adv_group.add_argument("--allow-kv-cache-translation", action="store_true", help="Allow KV cache translation")
        adv_group.add_argument("--force-kv-cache-translation", action="store_true", help="Force KV cache translation")
        adv_group.add_argument("--use-sparse-ot", action="store_true", help="Use sparse OT projection")
        adv_group.add_argument(
            "--shared-chat-template",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Share chat template across models",
        )
        adv_group.add_argument("--alignment-strategy", type=str, help="Vocabulary alignment strategy")
        adv_group.add_argument("--use-abe", action="store_true", help="Enable Agreement-Based Ensembling")
        adv_group.add_argument("--use-stats-tracker", action="store_true", help="Track model statistics")
        adv_group.add_argument("--use-enhanced", action="store_true", help="Enable all enhanced features")
        adv_group.add_argument("--use-weighted-average", action="store_true", help="Use weighted average ensemble")
        adv_group.add_argument("--order-neutral", action="store_true", help="Order-neutral blending")
        adv_group.add_argument("--soft-swap", action="store_true", help="Enable soft swapping")
        adv_group.add_argument("--soft-swap-weight", type=float, help="Soft swap weight multiplier")
        adv_group.add_argument("--use-blending", action="store_true", help="Enable distribution blending")

        # Utility options
        util_group = parser.add_argument_group("Utilities")
        util_group.add_argument("--list-models", action="store_true", help="List available models")
        util_group.add_argument("--list-presets", action="store_true", help="List available presets")
        util_group.add_argument("--list-aliases", action="store_true", help="List model aliases")
        util_group.add_argument("--show-config", action="store_true", help="Show resolved config and exit")

        return parser.parse_args()

    def _list_presets(self) -> List[str]:
        """Get list of available presets."""
        return MindMeldCLIConfig.list_presets()

    def _get_epilog(self) -> str:
        """Generate help epilog with examples."""
        return """
Examples:
  # Load a config file directly
  %(prog)s my-config.yaml

  # Use a preset
  %(prog)s --preset creative --prompt "Once upon a time"

  # Quick models with aliases
  %(prog)s gemma-1b gemma-2b --blend dynamic

  # Models with personas
  %(prog)s gemma-1b@Optimist gemma-2b@Skeptic --preset debate

  # Override preset options
  %(prog)s --preset analytical --steps 100 --temperature 0.3

  # Full model spec with blending
  %(prog)s pytorch:google/gemma-3-1b-it pytorch:google/gemma-2-2b-it \\
      --blend smooth --strategy confidence

  # Save config for later
  %(prog)s gemma-1b gemma-2b --blend dynamic --save-config my-setup.yaml

Model Aliases (built-in):
  gemma-1b    -> pytorch:google/gemma-3-1b-it
  gemma-2b    -> pytorch:google/gemma-2-2b-it
  gemma-4b    -> pytorch:google/gemma-3-4b-it
  phi-mini    -> pytorch:microsoft/Phi-3.5-mini-instruct
  mistral-7b  -> pytorch:mistralai/Mistral-7B-v0.1

Blend Modes:
  hard     No blending, pure model switching
  soft     Gentle blending with soft swaps
  dynamic  Adaptive blending based on confidence
  smooth   Maximum interpolation between models
  0-100    Numeric blend strength (0=switching, 100=full blend)

Presets: """ + ", ".join(self._list_presets())

    def resolve_configuration(self, args: argparse.Namespace) -> MindMeldCLIConfig:
        """Resolve final configuration from all sources."""
        config_path = None
        preset = args.preset

        # Check if first positional arg is a YAML file
        if args.models_or_config and len(args.models_or_config) == 1:
            potential_config = args.models_or_config[0]
            if potential_config.endswith(('.yaml', '.yml')) and os.path.exists(potential_config):
                config_path = potential_config
                args.models_or_config = []

        # Build CLI overrides dict
        overrides = self._build_overrides(args)

        # Resolve config
        config = resolve_config(
            config_path=config_path or args.config,
            preset=preset,
            cli_overrides=overrides,
        )

        # Parse models from positional args or --models flag
        model_specs = args.models_or_config or args.models or []
        if model_specs:
            config.models = [
                ModelSpec.parse(spec, config.aliases) for spec in model_specs
            ]

        # Apply --persona flags to models
        if args.personas:
            for i, persona in enumerate(args.personas):
                if i < len(config.models):
                    config.models[i].persona = persona

        return config

    def _build_overrides(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Build override dict from CLI args."""
        overrides: Dict[str, Any] = {}

        # Simple fields
        if args.prompt:
            overrides["prompt"] = args.prompt
        if args.strategy:
            overrides["strategy"] = args.strategy
        if args.interval:
            overrides["interval"] = args.interval
        if args.prompt_system:
            overrides["prompt_system"] = args.prompt_system
        if args.prompt_chat_template is not None:
            overrides["prompt_chat_template"] = args.prompt_chat_template
        if args.no_default_system:
            overrides["no_default_system"] = True
        if args.stop_text:
            overrides["stop_text"] = args.stop_text
        if args.max_sentences:
            overrides["max_sentences"] = args.max_sentences
        if args.no_step_delay:
            overrides["no_step_delay"] = True

        # Blend options
        blend = {}
        if args.blend:
            blend_val = args.blend.lower()
            if blend_val in self.BLEND_MODES:
                blend["mode"] = blend_val
                blend["enabled"] = blend_val != "hard"
            elif blend_val.isdigit():
                strength = int(blend_val)
                blend["strength"] = max(0, min(100, strength))
                blend["enabled"] = strength > 0
        if args.blend_strategy:
            blend["strategy"] = args.blend_strategy
        if args.soft_swap:
            blend["soft_swap"] = True
        if args.soft_swap_weight:
            blend["soft_swap_weight"] = args.soft_swap_weight
        if args.order_neutral:
            blend["order_neutral"] = True
        if args.use_blending:
            blend["enabled"] = True
        if args.use_weighted_average:
            blend["enabled"] = True
            blend["strategy"] = "weighted_average"
        if blend:
            overrides["blend"] = blend

        # Generation options
        generation = {}
        if args.steps:
            generation["steps"] = args.steps
        if args.temperature:
            generation["temperature"] = args.temperature
        if args.top_k:
            generation["top_k"] = args.top_k
        if args.top_p:
            generation["top_p"] = args.top_p
        if args.repetition_penalty:
            generation["repetition_penalty"] = args.repetition_penalty
        if generation:
            overrides["generation"] = generation

        # Output options
        output = {}
        if args.output:
            output["format"] = args.output
        if args.verbose:
            output["verbose"] = True
        if args.summary_only:
            output["summary_only"] = True
        if args.headless:
            output["headless"] = True
        if args.show_attention is not None:
            output["show_attention"] = args.show_attention
        if args.stats_file:
            output["stats_file"] = args.stats_file
        if args.meld_diagnostics:
            output["meld_diagnostics"] = True
        if output:
            overrides["output"] = output

        # Advanced options
        advanced = {}
        if args.translate_logits:
            advanced["translate_logits"] = True
        if args.allow_kv_cache_translation:
            advanced["allow_kv_cache_translation"] = True
        if args.force_kv_cache_translation:
            advanced["force_kv_cache_translation"] = True
        if args.use_sparse_ot:
            advanced["use_sparse_ot"] = True
        if args.shared_chat_template is not None:
            advanced["shared_chat_template"] = args.shared_chat_template
        if args.alignment_strategy:
            advanced["alignment_strategy"] = args.alignment_strategy
        if args.use_abe:
            advanced["use_abe"] = True
        if args.use_stats_tracker:
            advanced["use_stats_tracker"] = True
        if args.use_enhanced:
            advanced["use_enhanced"] = True
        if advanced:
            overrides["advanced"] = advanced

        return overrides

    def validate_models(self, config: MindMeldCLIConfig) -> List[ModelSpec]:
        """Validate model specifications and return valid ones."""
        print("\n" + "=" * 70)
        print("Validating model specifications...")
        print("=" * 70)

        valid_models = []
        for model in config.models:
            spec = f"{model.engine}:{model.model}"
            result = ModelValidator.validate_model_spec(spec, require_logits=True)

            if not print_validation_result(result, spec):
                print(f"[X] Skipping invalid model: {spec}")
                print("   Mind melding requires engines with logits access.\n")
                continue

            valid_models.append(model)

        return valid_models

    def load_engines(self, models: List[ModelSpec], config: MindMeldCLIConfig) -> List[LLMEngine]:
        """Load model engines."""
        engines = []

        for model in models:
            print(ui.color_text(
                f"\n[+] Loading {model.model} with {model.engine} engine...",
                cfg.COLOR_CYAN
            ))

            try:
                engine_args = {
                    "engine": model.engine,
                    "model": model.model,
                    "temperature": config.generation.temperature,
                    "top_k": config.generation.top_k,
                    "top_p": config.generation.top_p,
                    "steps": config.generation.steps,
                    "verbose": config.output.verbose,
                    "show_attention": config.output.show_attention,
                    "pytorch_device_map": "auto",
                    "use_kv_cache": True,
                    "onnx_tokenizer": None,
                }

                engine = get_engine(model.engine, model.model, engine_args)
                print("Loading model...")
                engine.load()
                print(ui.color_text("[OK] Model loaded successfully!", cfg.COLOR_GREEN))
                engines.append(engine)

            except Exception as e:
                print(ui.color_text(f"[X] Failed to load {model.model}: {e}", cfg.COLOR_RED))
                if engines:
                    cont = input("Continue with loaded models? (y/n): ").strip().lower()
                    if cont != 'y':
                        return []

        return engines

    def run_meld(self, config: MindMeldCLIConfig, engines: List[LLMEngine]) -> Optional[Dict[str, Any]]:
        """Run the Mind Meld session."""
        if not config.output.summary_only and not config.output.headless:
            print(ui.color_text("\n[>] Starting Mind Meld Session", cfg.COLOR_GREEN))
            if config._preset_name:
                print(ui.color_text(f"    Preset: {config._preset_name}", cfg.COLOR_YELLOW))
            print("=" * 70)

        # Build args namespace for MindMeldMode
        meld_args = self._build_meld_args(config)

        try:
            meld_mode = MindMeldMode(engines, meld_args)
            result = meld_mode.run()

            # Format output based on config
            if config.output.format == "json":
                return self._format_json_output(config, result)
            elif config.output.format == "markdown":
                return self._format_markdown_output(config, result)

            return result

        except KeyboardInterrupt:
            print(ui.color_text("\n\n[!] Mind Meld interrupted by user", cfg.COLOR_YELLOW))
        except Exception as e:
            print(ui.color_text(f"\n\n[X] Error during Mind Meld: {e}", cfg.COLOR_RED))
            if config.output.verbose:
                import traceback
                traceback.print_exc()

        return None

    def _build_meld_args(self, config: MindMeldCLIConfig) -> argparse.Namespace:
        """Build args namespace for MindMeldMode."""
        # Apply blend mode settings
        config.blend.apply_mode()

        return argparse.Namespace(
            temperature=config.generation.temperature,
            top_k=config.generation.top_k,
            top_p=config.generation.top_p,
            steps=config.generation.steps,
            repetition_penalty=config.generation.repetition_penalty,
            verbose=config.output.verbose,
            show_attention=config.output.show_attention,
            swap_strategy=self.STRATEGY_MAP.get(config.strategy, SwapStrategy.PATTERN_BASED),
            fixed_interval=config.interval,
            confidence_threshold=0.5,
            perplexity_threshold=50.0,
            initial_prompt=config.prompt,
            no_step_delay=config.no_step_delay,
            summary_only=config.output.summary_only,
            stop_text=config.stop_text,
            max_sentences=config.max_sentences,
            prompt_chat_template=config.prompt_chat_template,
            prompt_system=config.prompt_system,
            personas=config.get_personas(),
            no_default_system=config.no_default_system,
            # Blend settings
            use_blending=config.blend.enabled,
            use_weighted_average=config.blend.enabled and config.blend.strategy == "weighted_average",
            order_neutral=config.blend.order_neutral,
            blend_strategy=config.blend.strategy,
            soft_swap=config.blend.soft_swap,
            soft_swap_weight=config.blend.soft_swap_weight,
            # Advanced settings
            use_enhanced=config.advanced.use_enhanced,
            use_abe=config.advanced.use_abe,
            use_stats_tracker=config.advanced.use_stats_tracker,
            stats_file=config.output.stats_file,
            meld_diagnostics=config.output.meld_diagnostics,
            allow_kv_cache_translation=config.advanced.allow_kv_cache_translation,
            force_kv_cache_translation=config.advanced.force_kv_cache_translation,
            translate_logits=config.advanced.translate_logits,
            use_sparse_ot=config.advanced.use_sparse_ot,
            shared_chat_template=config.advanced.shared_chat_template,
            alignment_strategy=config.advanced.alignment_strategy,
            headless=config.output.headless,
        )

    def _format_json_output(self, config: MindMeldCLIConfig, result: Any) -> Dict[str, Any]:
        """Format output as JSON."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "preset": config._preset_name,
                "models": [str(m) for m in config.models],
                "strategy": config.strategy,
                "blend_mode": config.blend.mode,
                "prompt": config.prompt,
            },
            "result": result if isinstance(result, dict) else {"output": str(result)},
        }
        print(json.dumps(output, indent=2))
        return output

    def _format_markdown_output(self, config: MindMeldCLIConfig, result: Any) -> Dict[str, Any]:
        """Format output as Markdown."""
        lines = [
            "# Mind Meld Session",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Configuration",
            "",
        ]

        if config._preset_name:
            lines.append(f"- **Preset:** {config._preset_name}")
        lines.append(f"- **Strategy:** {config.strategy}")
        lines.append(f"- **Blend Mode:** {config.blend.mode}")
        lines.append("")
        lines.append("### Models")
        for i, m in enumerate(config.models, 1):
            persona_str = f" ({m.persona})" if m.persona else ""
            lines.append(f"{i}. `{m.engine}:{m.model}`{persona_str}")
        lines.append("")
        lines.append("## Prompt")
        lines.append("")
        lines.append(f"> {config.prompt}")
        lines.append("")
        lines.append("## Output")
        lines.append("")
        lines.append("```")
        lines.append(str(result) if result else "(no output)")
        lines.append("```")

        print("\n".join(lines))
        return {"markdown": "\n".join(lines), "result": result}

    def list_models(self):
        """List available models."""
        print("=" * 70)
        print("Available Models for Mind Meld")
        print("=" * 70)

        # Ollama models
        print("\n[Ollama] Models (from 'ollama list'):")
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    parts = line.split()
                    if parts:
                        print(f"  ollama:{parts[0]}")
            else:
                print("  (Ollama not available)")
        except Exception as e:
            print(f"  (Error: {e})")

        # HuggingFace cache
        print("\n[HuggingFace] Cached models:")
        hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
        if os.path.exists(hf_cache):
            cached = [d for d in os.listdir(hf_cache) if d.startswith('models--')]
            for model_dir in sorted(cached)[:15]:
                model_name = model_dir.replace('models--', '').replace('--', '/')
                print(f"  pytorch:{model_name}")
            if len(cached) > 15:
                print(f"  ... and {len(cached) - 15} more")
        else:
            print("  (No cached models)")

    def list_presets(self):
        """List available presets with descriptions."""
        print("=" * 70)
        print("Available Mind Meld Presets")
        print("=" * 70)

        for name in sorted(MindMeldCLIConfig.list_presets()):
            try:
                config = MindMeldCLIConfig.load_preset(name)
                models = ", ".join(m.model.split("/")[-1] for m in config.models)
                blend = config.blend.mode if config.blend.enabled else "switching"
                print(f"\n  {name}")
                print(f"    Models: {models}")
                print(f"    Strategy: {config.strategy}, Blend: {blend}")
                if config.models and config.models[0].persona:
                    print(f"    Personas: Yes")
            except Exception as e:
                print(f"\n  {name}")
                print(f"    (Error loading: {e})")

        print("\n" + "=" * 70)
        print("Usage: mind-meld --preset <name> [options]")

    def list_aliases(self):
        """List model aliases."""
        print("=" * 70)
        print("Model Aliases")
        print("=" * 70)

        aliases = MindMeldCLIConfig.get_default_aliases()

        print("\n[Built-in Aliases]")
        for alias, full in sorted(aliases.items()):
            print(f"  {alias:15} -> {full}")

        # Check for user aliases
        from src.mind_meld.cli.config import load_user_aliases, USER_CONFIG_PATH
        user_aliases = load_user_aliases()
        if user_aliases:
            print(f"\n[User Aliases] (from {USER_CONFIG_PATH})")
            for alias, full in sorted(user_aliases.items()):
                print(f"  {alias:15} -> {full}")

        print("\n" + "=" * 70)
        print("Usage: mind-meld <alias> <alias> [options]")
        print("       mind-meld <alias>@<persona> <alias>@<persona>")

    def show_config(self, config: MindMeldCLIConfig):
        """Show resolved configuration."""
        print("=" * 70)
        print("Resolved Configuration")
        print("=" * 70)

        import yaml
        print(yaml.dump(config.to_dict(), default_flow_style=False, sort_keys=False))

    def run(self):
        """Main entry point."""
        args = self.parse_args()

        # Handle utility commands
        if args.list_models:
            self.list_models()
            return

        if args.list_presets:
            self.list_presets()
            return

        if args.list_aliases:
            self.list_aliases()
            return

        # Resolve configuration
        try:
            config = self.resolve_configuration(args)
        except Exception as e:
            print(ui.color_text(f"[X] Configuration error: {e}", cfg.COLOR_RED))
            return

        # Handle --show-config
        if args.show_config:
            self.show_config(config)
            return

        # Handle --save-config
        if args.save_config:
            config.save_yaml(args.save_config)
            print(f"Configuration saved to: {args.save_config}")
            return

        # Validate we have models
        if not config.models:
            print(ui.color_text(
                "[X] No models specified. Use positional args, --models, --preset, or config file.",
                cfg.COLOR_RED
            ))
            print("\nExamples:")
            print("  mind-meld gemma-1b gemma-2b --prompt 'Hello'")
            print("  mind-meld --preset creative")
            print("  mind-meld my-config.yaml")
            return

        if len(config.models) < 2:
            print(ui.color_text("[X] Mind Meld requires at least 2 models.", cfg.COLOR_RED))
            return

        # Validate models
        valid_models = self.validate_models(config)
        if len(valid_models) < 2:
            print(ui.color_text(
                f"\n[X] Need at least 2 valid models, only {len(valid_models)} passed validation.",
                cfg.COLOR_RED
            ))
            return

        config.models = valid_models
        print(f"\n[OK] Validated {len(valid_models)} model(s) for mind melding\n")

        # Load engines
        engines = self.load_engines(valid_models, config)
        if not engines or len(engines) < 2:
            print(ui.color_text("[X] Failed to load sufficient models", cfg.COLOR_RED))
            return

        # Run meld
        self.run_meld(config, engines)


def main():
    """Main entry point."""
    cli = MindMeldCLI()
    cli.run()


if __name__ == "__main__":
    main()
