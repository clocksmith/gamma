"""
Pre-configured Mind Meld presets for common use cases.

Makes it easy to get started with optimal configurations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

from src.mind_meld.core.config import MeldConfig, SwapStrategy


class PresetType(Enum):
    """Types of presets available."""
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    TECHNICAL_WRITING = "technical_writing"
    FAST_GENERATION = "fast_generation"
    MAX_QUALITY = "max_quality"
    RESEARCH_ANALYSIS = "research_analysis"
    CONVERSATION = "conversation"
    TRANSLATION = "translation"


@dataclass
class MeldPreset:
    """A complete Mind Meld preset configuration."""
    name: str
    description: str
    models: List[str]  # Model names/aliases from registry
    strategy: str
    temperature: float
    top_k: int
    top_p: float
    use_speculative: bool = False
    use_contrastive: bool = False
    use_abe: bool = False
    use_moe: bool = False
    use_feedback: bool = False
    use_hierarchical: bool = False
    use_adversarial: bool = False
    max_tokens: int = 100
    additional_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_config is None:
            self.additional_config = {}


# ============================================================================
# PRESET DEFINITIONS
# ============================================================================

PRESETS = {
    PresetType.CREATIVE_WRITING: MeldPreset(
        name="Creative Writing",
        description="Optimized for creative content like stories, poetry, and brainstorming",
        models=['gemma_2_2b', 'qwen_1.5b'],  # Creative + fast
        strategy='pattern',  # Swap at sentence boundaries
        temperature=0.9,  # High creativity
        top_k=100,
        top_p=0.95,
        use_contrastive=False,  # Don't want too constrained
        use_abe=False,  # Want diversity
        use_feedback=True,  # Self-critique helps quality
        max_tokens=200,
        additional_config={
            'swap_on_punctuation': True,
            'min_tokens_per_swap': 10
        }
    ),

    PresetType.CODE_GENERATION: MeldPreset(
        name="Code Generation",
        description="Optimized for generating code with high accuracy",
        models=['codellama_7b', 'gemma_2_9b'],  # Code specialist + reasoning
        strategy='semantic',  # Swap on context changes
        temperature=0.2,  # Low for accuracy
        top_k=40,
        top_p=0.9,
        use_abe=True,  # Agreement for correctness
        use_moe=True,  # Route code vs comments differently
        use_feedback=True,  # Validate code quality
        max_tokens=300,
        additional_config={
            'prefer_code_specialist': True,
            'validate_syntax': True
        }
    ),

    PresetType.TECHNICAL_WRITING: MeldPreset(
        name="Technical Writing",
        description="For documentation, technical explanations, and analysis",
        models=['gemma_2_9b', 'gemma_7b'],  # Strong reasoning models
        strategy='perplexity',  # Swap when uncertain
        temperature=0.6,
        top_k=50,
        top_p=0.92,
        use_hierarchical=True,  # Plan structure
        use_feedback=True,  # Ensure clarity
        use_adversarial=True,  # Fact-check claims
        max_tokens=250,
        additional_config={
            'perplexity_threshold': 40.0,
            'hierarchical_planning': True
        }
    ),

    PresetType.FAST_GENERATION: MeldPreset(
        name="Fast Generation",
        description="Maximum speed with acceptable quality",
        models=['tinyllama', 'qwen_1.5b'],  # Smallest/fastest models
        strategy='fixed',  # Simple fixed interval
        temperature=0.7,
        top_k=40,
        top_p=0.9,
        use_speculative=True,  # 2-3x speedup!
        use_abe=False,  # Avoid overhead
        max_tokens=150,
        additional_config={
            'fixed_interval': 10,
            'speculative_k': 4,
            'draft_model': 'tinyllama',
            'target_model': 'qwen_1.5b'
        }
    ),

    PresetType.MAX_QUALITY: MeldPreset(
        name="Maximum Quality",
        description="Best possible output quality, slower generation",
        models=['gemma_2_9b', 'mistral_7b'],  # Best models
        strategy='perplexity',
        temperature=0.5,
        top_k=50,
        top_p=0.95,
        use_contrastive=True,  # Amplify expert capabilities
        use_abe=True,  # Agreement for accuracy
        use_feedback=True,  # Iterative refinement
        use_adversarial=True,  # Fact-check
        max_tokens=200,
        additional_config={
            'contrastive_alpha': 0.6,
            'feedback_iterations': 3,
            'adversarial_rounds': 2,
            'perplexity_threshold': 30.0
        }
    ),

    PresetType.RESEARCH_ANALYSIS: MeldPreset(
        name="Research & Analysis",
        description="Deep analysis with fact-checking and structured output",
        models=['gemma_2_9b', 'mathstral'],  # Reasoning + math
        strategy='perplexity',
        temperature=0.4,
        top_k=40,
        top_p=0.9,
        use_hierarchical=True,  # Structured approach
        use_adversarial=True,  # Critical analysis
        use_feedback=True,  # Refinement
        max_tokens=300,
        additional_config={
            'hierarchical_steps': 5,
            'adversarial_debate': True,
            'fact_checking': True
        }
    ),

    PresetType.CONVERSATION: MeldPreset(
        name="Conversation",
        description="Natural, engaging dialogue",
        models=['gemma_2_2b', 'qwen_1.5b'],
        strategy='pattern',  # Swap at natural breaks
        temperature=0.8,
        top_k=80,
        top_p=0.95,
        use_moe=True,  # Route by conversation context
        max_tokens=150,
        additional_config={
            'pattern': ['?', '!', '.', '\n'],
            'maintain_personality': True
        }
    ),

    PresetType.TRANSLATION: MeldPreset(
        name="Translation",
        description="High-accuracy translation with validation",
        models=['aya', 'gemma_2_9b'],  # Multilingual + reasoning
        strategy='fixed',
        temperature=0.3,  # Low for accuracy
        top_k=30,
        top_p=0.85,
        use_abe=True,  # Agreement crucial for translation
        use_feedback=True,  # Validate translation
        max_tokens=200,
        additional_config={
            'fixed_interval': 5,
            'back_translation_check': True
        }
    ),
}


def get_preset(preset_type: PresetType) -> MeldPreset:
    """Get a preset configuration."""
    return PRESETS[preset_type]


def list_presets() -> List[Tuple[PresetType, str]]:
    """List available presets with descriptions."""
    return [(ptype, preset.description) for ptype, preset in PRESETS.items()]


def get_preset_by_name(name: str) -> Optional[MeldPreset]:
    """Get preset by name (case-insensitive)."""
    name_lower = name.lower().replace(' ', '_')
    for preset_type, preset in PRESETS.items():
        if preset_type.value == name_lower or preset.name.lower().replace(' ', '_') == name_lower:
            return preset
    return None


def create_custom_preset(
    name: str,
    models: List[str],
    strategy: str = 'pattern',
    **kwargs
) -> MeldPreset:
    """
    Create a custom preset.

    Args:
        name: Preset name
        models: List of model names
        strategy: Swap strategy
        **kwargs: Additional configuration

    Returns:
        Custom MeldPreset
    """
    return MeldPreset(
        name=name,
        description=kwargs.get('description', 'Custom preset'),
        models=models,
        strategy=strategy,
        temperature=kwargs.get('temperature', 0.7),
        top_k=kwargs.get('top_k', 50),
        top_p=kwargs.get('top_p', 0.95),
        use_speculative=kwargs.get('use_speculative', False),
        use_contrastive=kwargs.get('use_contrastive', False),
        use_abe=kwargs.get('use_abe', False),
        use_moe=kwargs.get('use_moe', False),
        use_feedback=kwargs.get('use_feedback', False),
        use_hierarchical=kwargs.get('use_hierarchical', False),
        use_adversarial=kwargs.get('use_adversarial', False),
        max_tokens=kwargs.get('max_tokens', 100),
        additional_config=kwargs.get('additional_config', {})
    )


# ============================================================================
# PRESET APPLICATION HELPERS
# ============================================================================

def apply_preset_to_args(preset: MeldPreset, args: Any):
    """Apply preset configuration to argparse args."""
    args.temperature = preset.temperature
    args.top_k = preset.top_k
    args.top_p = preset.top_p
    args.steps = preset.max_tokens
    args.swap_strategy = preset.strategy

    # Advanced features
    args.use_speculative = preset.use_speculative
    args.use_contrastive = preset.use_contrastive
    args.use_abe = preset.use_abe
    args.use_moe = preset.use_moe
    args.use_feedback = preset.use_feedback
    args.use_hierarchical = preset.use_hierarchical
    args.use_adversarial = preset.use_adversarial

    # Additional config
    for key, value in preset.additional_config.items():
        setattr(args, key, value)


def get_recommended_preset(task_description: str) -> MeldPreset:
    """
    Recommend a preset based on task description.

    Args:
        task_description: Description of the task

    Returns:
        Recommended preset
    """
    desc_lower = task_description.lower()

    # Keyword matching
    if any(kw in desc_lower for kw in ['code', 'program', 'function', 'debug']):
        return get_preset(PresetType.CODE_GENERATION)
    elif any(kw in desc_lower for kw in ['creative', 'story', 'poem', 'brainstorm']):
        return get_preset(PresetType.CREATIVE_WRITING)
    elif any(kw in desc_lower for kw in ['technical', 'document', 'explain', 'analysis']):
        return get_preset(PresetType.TECHNICAL_WRITING)
    elif any(kw in desc_lower for kw in ['fast', 'quick', 'speed']):
        return get_preset(PresetType.FAST_GENERATION)
    elif any(kw in desc_lower for kw in ['best', 'quality', 'perfect']):
        return get_preset(PresetType.MAX_QUALITY)
    elif any(kw in desc_lower for kw in ['research', 'analyze', 'study']):
        return get_preset(PresetType.RESEARCH_ANALYSIS)
    elif any(kw in desc_lower for kw in ['chat', 'conversation', 'talk']):
        return get_preset(PresetType.CONVERSATION)
    elif any(kw in desc_lower for kw in ['translate', 'translation']):
        return get_preset(PresetType.TRANSLATION)
    else:
        # Default to balanced
        return get_preset(PresetType.CONVERSATION)
