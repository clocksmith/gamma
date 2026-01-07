"""
Mind Meld CLI Configuration System

Provides YAML-based configuration with:
- Preset profiles (creative, analytical, debate, etc.)
- Model aliases for shorter commands
- CLI flag overrides that merge into configs
- Persona binding syntax (model@persona)
"""

import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


# Default paths
CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "configs" / "mind_meld"
PRESETS_DIR = CONFIG_DIR / "presets"
USER_CONFIG_PATH = Path.home() / ".mind-meld.yaml"


@dataclass
class ModelSpec:
    """Specification for a single model in the meld."""
    engine: str
    model: str
    persona: Optional[str] = None
    weight: float = 1.0

    @classmethod
    def parse(cls, spec: str, aliases: Optional[Dict[str, str]] = None) -> "ModelSpec":
        """
        Parse model specification string.

        Formats supported:
        - "engine:model" -> ModelSpec(engine, model)
        - "engine:model@persona" -> ModelSpec(engine, model, persona)
        - "alias" -> resolved via aliases dict
        - "alias@persona" -> alias resolved, persona extracted
        - "model" (no colon) -> defaults to pytorch engine
        """
        aliases = aliases or {}

        # Extract persona if present (model@persona syntax)
        persona = None
        if "@" in spec:
            spec, persona = spec.rsplit("@", 1)

        # Check if it's an alias
        if spec in aliases:
            resolved = aliases[spec]
            # Resolved alias might be "engine:model" format
            if ":" in resolved:
                engine, model = resolved.split(":", 1)
            else:
                engine, model = "pytorch", resolved
        elif ":" in spec:
            engine, model = spec.split(":", 1)
        else:
            # Default to pytorch engine
            engine = "pytorch"
            model = spec

        return cls(engine=engine, model=model, persona=persona)

    def to_tuple(self) -> Tuple[str, str]:
        """Return (engine, model) tuple for compatibility."""
        return (self.engine, self.model)

    def __str__(self) -> str:
        s = f"{self.engine}:{self.model}"
        if self.persona:
            s += f"@{self.persona}"
        return s


@dataclass
class BlendConfig:
    """Configuration for model blending behavior."""
    enabled: bool = False
    mode: str = "dynamic"  # hard, soft, dynamic, smooth
    strategy: str = "weighted_average"
    soft_swap: bool = False
    soft_swap_weight: float = 0.3
    order_neutral: bool = False

    # Simplified blend strength (0-100)
    # 0 = pure switching, 100 = full blending
    strength: int = 50

    def apply_mode(self):
        """Apply mode presets to detailed settings."""
        if self.mode == "hard":
            self.enabled = False
            self.soft_swap = False
        elif self.mode == "soft":
            self.enabled = True
            self.soft_swap = True
            self.soft_swap_weight = 0.3
        elif self.mode == "dynamic":
            self.enabled = True
            self.soft_swap = True
            self.strategy = "dynamic_weighted"
        elif self.mode == "smooth":
            self.enabled = True
            self.soft_swap = True
            self.soft_swap_weight = 0.5
            self.order_neutral = True


@dataclass
class GenerationConfig:
    """Generation parameters."""
    steps: int = 30
    temperature: float = 0.7
    top_k: int = 8
    top_p: float = 0.95
    repetition_penalty: float = 1.1


@dataclass
class OutputConfig:
    """Output format configuration."""
    format: str = "terminal"  # terminal, json, markdown
    verbose: bool = False
    show_attention: bool = True
    summary_only: bool = False
    headless: bool = False
    stats_file: Optional[str] = None
    meld_diagnostics: bool = False


@dataclass
class AdvancedConfig:
    """Advanced/experimental settings."""
    translate_logits: bool = False
    allow_kv_cache_translation: bool = False
    force_kv_cache_translation: bool = False
    use_sparse_ot: bool = False
    shared_chat_template: Optional[bool] = None
    alignment_strategy: str = "semantic"
    use_abe: bool = False
    use_stats_tracker: bool = False
    use_enhanced: bool = False


@dataclass
class MindMeldCLIConfig:
    """
    Main configuration class for Mind Meld CLI.

    Supports loading from:
    - YAML config files
    - Preset profiles
    - CLI arguments (as overrides)
    """
    # Models to meld
    models: List[ModelSpec] = field(default_factory=list)

    # Model aliases for convenience
    aliases: Dict[str, str] = field(default_factory=dict)

    # Strategy
    strategy: str = "pattern"
    interval: int = 8

    # Prompt
    prompt: str = "In a world where two minds are better than one,"
    prompt_system: Optional[str] = None
    prompt_chat_template: Optional[bool] = None
    no_default_system: bool = False

    # Sub-configs
    blend: BlendConfig = field(default_factory=BlendConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)

    # Stop conditions
    stop_text: List[str] = field(default_factory=list)
    max_sentences: Optional[int] = None
    no_step_delay: bool = False

    # Preset that was loaded (for reference)
    _preset_name: Optional[str] = field(default=None, repr=False)

    @classmethod
    def get_default_aliases(cls) -> Dict[str, str]:
        """Return default model aliases."""
        return {
            # Gemma shortcuts
            "gemma-1b": "pytorch:google/gemma-3-1b-it",
            "gemma-2b": "pytorch:google/gemma-2-2b-it",
            "gemma-4b": "pytorch:google/gemma-3-4b-it",
            "gemma3-1b": "pytorch:google/gemma-3-1b-it",
            "gemma2-2b": "pytorch:google/gemma-2-2b-it",

            # Phi shortcuts
            "phi-mini": "pytorch:microsoft/Phi-3.5-mini-instruct",

            # Mistral shortcuts
            "mistral-7b": "pytorch:mistralai/Mistral-7B-v0.1",

            # MLX shortcuts (Apple Silicon)
            "mlx-gemma": "mlx:mlx-community/gemma-3-1b-it-4bit",
        }

    @classmethod
    def load_yaml(cls, path: Union[str, Path]) -> "MindMeldCLIConfig":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    @classmethod
    def load_preset(cls, name: str) -> "MindMeldCLIConfig":
        """Load a preset configuration by name."""
        # Check built-in presets
        preset_path = PRESETS_DIR / f"{name}.yaml"
        if preset_path.exists():
            config = cls.load_yaml(preset_path)
            config._preset_name = name
            return config

        # Check user presets
        user_presets = USER_CONFIG_PATH.parent / "mind-meld-presets"
        if user_presets.exists():
            user_preset = user_presets / f"{name}.yaml"
            if user_preset.exists():
                config = cls.load_yaml(user_preset)
                config._preset_name = name
                return config

        raise ValueError(f"Unknown preset: {name}. Available: {cls.list_presets()}")

    @classmethod
    def list_presets(cls) -> List[str]:
        """List available preset names."""
        presets = []
        if PRESETS_DIR.exists():
            presets.extend(p.stem for p in PRESETS_DIR.glob("*.yaml"))
        return sorted(set(presets))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MindMeldCLIConfig":
        """Create config from dictionary (parsed YAML)."""
        config = cls()

        # Load aliases first (needed for model parsing)
        config.aliases = {**cls.get_default_aliases(), **data.get("aliases", {})}

        # Parse models
        if "models" in data:
            models_data = data["models"]
            if isinstance(models_data, list):
                for m in models_data:
                    if isinstance(m, str):
                        config.models.append(ModelSpec.parse(m, config.aliases))
                    elif isinstance(m, dict):
                        spec = ModelSpec(
                            engine=m.get("engine", "pytorch"),
                            model=m["model"],
                            persona=m.get("persona"),
                            weight=m.get("weight", 1.0),
                        )
                        config.models.append(spec)

        # Simple fields
        config.strategy = data.get("strategy", config.strategy)
        config.interval = data.get("interval", config.interval)
        config.prompt = data.get("prompt", config.prompt)
        config.prompt_system = data.get("prompt_system")
        config.prompt_chat_template = data.get("prompt_chat_template")
        config.no_default_system = data.get("no_default_system", False)
        config.stop_text = data.get("stop_text", [])
        config.max_sentences = data.get("max_sentences")
        config.no_step_delay = data.get("no_step_delay", False)

        # Blend config
        if "blend" in data:
            b = data["blend"]
            config.blend = BlendConfig(
                enabled=b.get("enabled", False),
                mode=b.get("mode", "dynamic"),
                strategy=b.get("strategy", "weighted_average"),
                soft_swap=b.get("soft_swap", False),
                soft_swap_weight=b.get("soft_swap_weight", 0.3),
                order_neutral=b.get("order_neutral", False),
                strength=b.get("strength", 50),
            )
            config.blend.apply_mode()

        # Generation config
        if "generation" in data:
            g = data["generation"]
            config.generation = GenerationConfig(
                steps=g.get("steps", 30),
                temperature=g.get("temperature", 0.7),
                top_k=g.get("top_k", 8),
                top_p=g.get("top_p", 0.95),
                repetition_penalty=g.get("repetition_penalty", 1.1),
            )

        # Output config
        if "output" in data:
            o = data["output"]
            config.output = OutputConfig(
                format=o.get("format", "terminal"),
                verbose=o.get("verbose", False),
                show_attention=o.get("show_attention", True),
                summary_only=o.get("summary_only", False),
                headless=o.get("headless", False),
                stats_file=o.get("stats_file"),
                meld_diagnostics=o.get("meld_diagnostics", False),
            )

        # Advanced config
        if "advanced" in data:
            a = data["advanced"]
            config.advanced = AdvancedConfig(
                translate_logits=a.get("translate_logits", False),
                allow_kv_cache_translation=a.get("allow_kv_cache_translation", False),
                force_kv_cache_translation=a.get("force_kv_cache_translation", False),
                use_sparse_ot=a.get("use_sparse_ot", False),
                shared_chat_template=a.get("shared_chat_template"),
                alignment_strategy=a.get("alignment_strategy", "semantic"),
                use_abe=a.get("use_abe", False),
                use_stats_tracker=a.get("use_stats_tracker", False),
                use_enhanced=a.get("use_enhanced", False),
            )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for YAML export."""
        return {
            "models": [
                {
                    "engine": m.engine,
                    "model": m.model,
                    **({"persona": m.persona} if m.persona else {}),
                    **({"weight": m.weight} if m.weight != 1.0 else {}),
                }
                for m in self.models
            ],
            "aliases": {k: v for k, v in self.aliases.items()
                       if k not in self.get_default_aliases()},
            "strategy": self.strategy,
            "interval": self.interval,
            "prompt": self.prompt,
            **({"prompt_system": self.prompt_system} if self.prompt_system else {}),
            **({"prompt_chat_template": self.prompt_chat_template}
               if self.prompt_chat_template is not None else {}),
            "blend": {
                "enabled": self.blend.enabled,
                "mode": self.blend.mode,
                "strategy": self.blend.strategy,
                "soft_swap": self.blend.soft_swap,
                "soft_swap_weight": self.blend.soft_swap_weight,
                "order_neutral": self.blend.order_neutral,
                "strength": self.blend.strength,
            },
            "generation": {
                "steps": self.generation.steps,
                "temperature": self.generation.temperature,
                "top_k": self.generation.top_k,
                "top_p": self.generation.top_p,
                "repetition_penalty": self.generation.repetition_penalty,
            },
            "output": {
                "format": self.output.format,
                "verbose": self.output.verbose,
                "show_attention": self.output.show_attention,
                "summary_only": self.output.summary_only,
                "headless": self.output.headless,
                **({"stats_file": self.output.stats_file} if self.output.stats_file else {}),
                "meld_diagnostics": self.output.meld_diagnostics,
            },
            "advanced": {
                "translate_logits": self.advanced.translate_logits,
                "allow_kv_cache_translation": self.advanced.allow_kv_cache_translation,
                "force_kv_cache_translation": self.advanced.force_kv_cache_translation,
                "use_sparse_ot": self.advanced.use_sparse_ot,
                **({"shared_chat_template": self.advanced.shared_chat_template}
                   if self.advanced.shared_chat_template is not None else {}),
                "alignment_strategy": self.advanced.alignment_strategy,
                "use_abe": self.advanced.use_abe,
                "use_stats_tracker": self.advanced.use_stats_tracker,
                "use_enhanced": self.advanced.use_enhanced,
            },
            **({"stop_text": self.stop_text} if self.stop_text else {}),
            **({"max_sentences": self.max_sentences} if self.max_sentences else {}),
            "no_step_delay": self.no_step_delay,
        }

    def save_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration to YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    def merge(self, overrides: Dict[str, Any]) -> "MindMeldCLIConfig":
        """
        Merge CLI overrides into this config, returning new config.

        CLI args take precedence over config file values.
        """
        # Start with current config as dict
        data = self.to_dict()

        # Deep merge overrides
        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if value is None:
                    continue
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = deep_merge(data, overrides)
        return MindMeldCLIConfig.from_dict(merged)

    def get_model_tuples(self) -> List[Tuple[str, str]]:
        """Return models as list of (engine, model) tuples."""
        return [m.to_tuple() for m in self.models]

    def get_personas(self) -> Optional[List[str]]:
        """Return list of personas if any models have them."""
        personas = [m.persona for m in self.models]
        if any(p is not None for p in personas):
            # Fill in None with empty strings for models without personas
            return [p or "" for p in personas]
        return None


def load_user_aliases() -> Dict[str, str]:
    """Load user-defined aliases from ~/.mind-meld.yaml"""
    if USER_CONFIG_PATH.exists():
        with open(USER_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f) or {}
        return data.get("aliases", {})
    return {}


def resolve_config(
    config_path: Optional[str] = None,
    preset: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> MindMeldCLIConfig:
    """
    Resolve final configuration from multiple sources.

    Priority (highest to lowest):
    1. CLI overrides
    2. Config file (if provided)
    3. Preset (if provided)
    4. Defaults
    """
    # Start with defaults or preset
    if preset:
        config = MindMeldCLIConfig.load_preset(preset)
    else:
        config = MindMeldCLIConfig()

    # Load user aliases
    user_aliases = load_user_aliases()
    config.aliases = {**config.aliases, **user_aliases}

    # Apply config file if provided
    if config_path:
        file_config = MindMeldCLIConfig.load_yaml(config_path)
        config = config.merge(file_config.to_dict())

    # Apply CLI overrides
    if cli_overrides:
        config = config.merge(cli_overrides)

    return config
