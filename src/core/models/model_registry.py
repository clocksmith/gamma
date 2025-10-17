"""Model Registry for intelligent model selection and management."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class ModelSpecialization(Enum):
    """Model specialization categories."""
    CODE = "code"
    CREATIVE = "creative"
    REASONING = "reasoning"
    FAST = "fast"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    MATH = "math"
    MULTILINGUAL = "multilingual"


@dataclass
class ModelProfile:
    """Profile for a model including capabilities and requirements."""
    name: str
    engine: str
    size_mb: int
    specialization: ModelSpecialization
    min_vram_mb: int
    context_length: int
    strengths: List[str]
    description: str
    quantization_options: List[str] = field(default_factory=lambda: ["none", "4bit", "8bit"])
    recommended_temperature: float = 0.7
    recommended_top_k: int = 50
    recommended_top_p: float = 0.95
    supports_kv_cache: bool = True
    license: str = "apache-2.0"

    def estimate_vram_with_context(self, context_tokens: int = 2048) -> int:
        """Estimate VRAM usage including KV cache."""
        # Base model size
        base_vram = self.size_mb

        # KV cache estimation (rough): ~0.5MB per 1000 tokens
        kv_cache_mb = (context_tokens / 1000) * 0.5

        # Overhead for activations, gradients, etc.
        overhead_mb = 512

        return int(base_vram + kv_cache_mb + overhead_mb)

    def fits_in_vram(self, available_vram_mb: int, context_tokens: int = 2048) -> bool:
        """Check if model fits in available VRAM."""
        required = self.estimate_vram_with_context(context_tokens)
        return required <= available_vram_mb


# Comprehensive model zoo
MODEL_ZOO: Dict[str, ModelProfile] = {
    # Fast, small models
    'tinyllama': ModelProfile(
        name='TinyLlama/TinyLlama-1.1B-Chat-v1.0',
        engine='pytorch',
        size_mb=1100,
        specialization=ModelSpecialization.FAST,
        min_vram_mb=2048,
        context_length=2048,
        strengths=['speed', 'low_memory', 'conversational'],
        description='Ultra-fast 1.1B model, great for draft/speculative decoding',
        recommended_temperature=0.8
    ),

    'qwen_1.5b': ModelProfile(
        name='Qwen/Qwen2-1.5B-Instruct',
        engine='pytorch',
        size_mb=1500,
        specialization=ModelSpecialization.CONVERSATIONAL,
        min_vram_mb=2048,
        context_length=32768,
        strengths=['creative_writing', 'brainstorming', 'speed', 'long_context'],
        description='Fast 1.5B model with excellent long context support',
        recommended_temperature=0.9
    ),

    # Gemma models
    'gemma_2b': ModelProfile(
        name='google/gemma-2b-it',
        engine='pytorch',
        size_mb=2000,
        specialization=ModelSpecialization.CONVERSATIONAL,
        min_vram_mb=3072,
        context_length=8192,
        strengths=['conversational', 'balanced', 'instruction_following'],
        description='Gemma 2B instruction-tuned, well-balanced performance',
        recommended_temperature=0.7
    ),

    'gemma_2_2b': ModelProfile(
        name='google/gemma-2-2b-it',
        engine='pytorch',
        size_mb=2000,
        specialization=ModelSpecialization.REASONING,
        min_vram_mb=3072,
        context_length=8192,
        strengths=['reasoning', 'instruction_following', 'accuracy'],
        description='Gemma 2 2B with improved reasoning capabilities',
        recommended_temperature=0.6
    ),

    'gemma_7b': ModelProfile(
        name='google/gemma-7b-it',
        engine='pytorch',
        size_mb=7000,
        specialization=ModelSpecialization.REASONING,
        min_vram_mb=8192,
        context_length=8192,
        strengths=['reasoning', 'technical', 'instruction_following'],
        description='Gemma 7B, strong reasoning and technical tasks',
        recommended_temperature=0.7
    ),

    'gemma_2_9b': ModelProfile(
        name='google/gemma-2-9b-it',
        engine='pytorch',
        size_mb=9000,
        specialization=ModelSpecialization.REASONING,
        min_vram_mb=12288,
        context_length=8192,
        strengths=['reasoning', 'technical', 'math', 'accuracy'],
        description='Gemma 2 9B, excellent reasoning and technical capabilities',
        recommended_temperature=0.6
    ),

    # Code models
    'codellama_7b': ModelProfile(
        name='codellama/CodeLlama-7b-Instruct-hf',
        engine='pytorch',
        size_mb=7000,
        specialization=ModelSpecialization.CODE,
        min_vram_mb=8192,
        context_length=16384,
        strengths=['code_generation', 'debugging', 'code_explanation'],
        description='CodeLlama 7B specialized for code generation',
        recommended_temperature=0.2
    ),

    'deepseek_coder': ModelProfile(
        name='deepseek-ai/deepseek-coder-6.7b-instruct',
        engine='pytorch',
        size_mb=6700,
        specialization=ModelSpecialization.CODE,
        min_vram_mb=8192,
        context_length=16384,
        strengths=['code_generation', 'multi_language', 'debugging'],
        description='DeepSeek Coder, excellent for multiple programming languages',
        recommended_temperature=0.3
    ),

    # Creative models
    'mistral_7b': ModelProfile(
        name='mistralai/Mistral-7B-Instruct-v0.2',
        engine='pytorch',
        size_mb=7000,
        specialization=ModelSpecialization.CREATIVE,
        min_vram_mb=8192,
        context_length=32768,
        strengths=['creative_writing', 'reasoning', 'long_context'],
        description='Mistral 7B with excellent creative writing and reasoning',
        recommended_temperature=0.9
    ),

    # Math/reasoning models
    'mathstral': ModelProfile(
        name='mistralai/mathstral-7B-v0.1',
        engine='pytorch',
        size_mb=7000,
        specialization=ModelSpecialization.MATH,
        min_vram_mb=8192,
        context_length=32768,
        strengths=['math', 'reasoning', 'technical', 'problem_solving'],
        description='Specialized for mathematical reasoning and problem solving',
        recommended_temperature=0.4
    ),

    # Multilingual
    'aya': ModelProfile(
        name='CohereForAI/aya-23-8B',
        engine='pytorch',
        size_mb=8000,
        specialization=ModelSpecialization.MULTILINGUAL,
        min_vram_mb=10240,
        context_length=8192,
        strengths=['multilingual', 'translation', 'cross_lingual'],
        description='Multilingual model supporting 100+ languages',
        recommended_temperature=0.7
    ),
}


class ModelSelector:
    """Intelligent model selection for Mind Meld ensembles."""

    def __init__(self, available_vram_mb: int):
        self.available_vram_mb = available_vram_mb

    def select_for_task(self, task: str, num_models: int = 2,
                       context_tokens: int = 2048) -> List[ModelProfile]:
        """Select best models for a given task."""
        task_lower = task.lower()

        # Determine primary specialization
        if any(kw in task_lower for kw in ['code', 'programming', 'debug', 'function']):
            priorities = [ModelSpecialization.CODE, ModelSpecialization.REASONING, ModelSpecialization.FAST]
        elif any(kw in task_lower for kw in ['creative', 'story', 'write', 'novel', 'poem']):
            priorities = [ModelSpecialization.CREATIVE, ModelSpecialization.CONVERSATIONAL, ModelSpecialization.FAST]
        elif any(kw in task_lower for kw in ['math', 'calculate', 'solve', 'equation']):
            priorities = [ModelSpecialization.MATH, ModelSpecialization.REASONING]
        elif any(kw in task_lower for kw in ['translate', 'language', 'multilingual']):
            priorities = [ModelSpecialization.MULTILINGUAL, ModelSpecialization.CONVERSATIONAL]
        elif any(kw in task_lower for kw in ['technical', 'explain', 'analyze']):
            priorities = [ModelSpecialization.TECHNICAL, ModelSpecialization.REASONING]
        else:
            priorities = [ModelSpecialization.CONVERSATIONAL, ModelSpecialization.REASONING, ModelSpecialization.FAST]

        # Filter models that fit in VRAM
        candidates = [
            model for model in MODEL_ZOO.values()
            if model.fits_in_vram(self.available_vram_mb // num_models, context_tokens)
        ]

        if not candidates:
            # Fall back to smallest models
            return sorted(MODEL_ZOO.values(), key=lambda m: m.size_mb)[:num_models]

        # Select diverse ensemble based on priorities
        selected = []
        for priority in priorities:
            matches = [m for m in candidates if m.specialization == priority and m not in selected]
            if matches:
                # Pick the largest that fits
                best = max(matches, key=lambda m: m.size_mb)
                selected.append(best)
                if len(selected) >= num_models:
                    break

        # Fill remaining slots with diverse options
        while len(selected) < num_models:
            remaining = [m for m in candidates if m not in selected]
            if not remaining:
                break
            # Pick most different specialization
            used_specs = {m.specialization for m in selected}
            different = [m for m in remaining if m.specialization not in used_specs]
            if different:
                selected.append(max(different, key=lambda m: m.size_mb))
            else:
                selected.append(remaining[0])

        return selected[:num_models]

    def select_for_strategy(self, strategy: str, task: str = "",
                          num_models: int = 2) -> List[ModelProfile]:
        """Select models optimized for a specific Mind Meld strategy."""
        if strategy == 'speculative':
            # Need one fast (draft) and one quality (target)
            draft = min(MODEL_ZOO.values(), key=lambda m: m.size_mb)
            target_candidates = [m for m in MODEL_ZOO.values() if m.size_mb > draft.size_mb * 3]
            target = max(target_candidates, key=lambda m: m.size_mb) if target_candidates else draft
            return [draft, target]

        elif strategy == 'contrastive':
            # Need expert and amateur (amateur should be 3-5x smaller)
            expert = max(MODEL_ZOO.values(),
                        key=lambda m: m.size_mb if m.fits_in_vram(self.available_vram_mb * 0.7) else 0)
            target_size = expert.size_mb // 4
            amateur = min(MODEL_ZOO.values(),
                         key=lambda m: abs(m.size_mb - target_size))
            return [expert, amateur]

        elif strategy == 'moe':
            # Need diverse specialists
            specializations = [
                ModelSpecialization.CODE,
                ModelSpecialization.CREATIVE,
                ModelSpecialization.REASONING,
                ModelSpecialization.FAST
            ]
            selected = []
            for spec in specializations:
                matches = [m for m in MODEL_ZOO.values()
                          if m.specialization == spec and m.fits_in_vram(self.available_vram_mb // 4)]
                if matches:
                    selected.append(max(matches, key=lambda m: m.size_mb))
                if len(selected) >= num_models:
                    break
            return selected[:num_models]

        else:
            # Default task-based selection
            return self.select_for_task(task, num_models)

    def recommend_configuration(self, models: List[ModelProfile]) -> Dict[str, any]:
        """Recommend optimal configuration for selected models."""
        # Average recommended settings
        avg_temp = sum(m.recommended_temperature for m in models) / len(models)
        avg_top_k = int(sum(m.recommended_top_k for m in models) / len(models))
        avg_top_p = sum(m.recommended_top_p for m in models) / len(models)

        # Detect if this looks like a code task
        has_code_model = any(m.specialization == ModelSpecialization.CODE for m in models)

        return {
            'temperature': 0.3 if has_code_model else avg_temp,
            'top_k': avg_top_k,
            'top_p': avg_top_p,
            'use_kv_cache': all(m.supports_kv_cache for m in models),
            'estimated_vram_mb': sum(m.estimate_vram_with_context() for m in models)
        }


def get_model_profile(model_name: str) -> Optional[ModelProfile]:
    """Get profile for a specific model by name or alias."""
    # Direct lookup
    if model_name in MODEL_ZOO:
        return MODEL_ZOO[model_name]

    # Search by full name
    for profile in MODEL_ZOO.values():
        if profile.name == model_name:
            return profile

    return None


def list_models_by_specialization(specialization: ModelSpecialization) -> List[ModelProfile]:
    """List all models with a specific specialization."""
    return [m for m in MODEL_ZOO.values() if m.specialization == specialization]


def get_recommended_ensemble(task: str, vram_budget_mb: int,
                            num_models: int = 2) -> List[Tuple[str, str]]:
    """
    Get recommended ensemble configuration for a task.

    Returns:
        List of (engine_type, model_name) tuples
    """
    selector = ModelSelector(vram_budget_mb)
    profiles = selector.select_for_task(task, num_models)

    return [(p.engine, p.name) for p in profiles]


if __name__ == "__main__":
    # Example usage
    selector = ModelSelector(available_vram_mb=16384)  # 16GB VRAM

    # Code task
    code_models = selector.select_for_task("Write a Python function to parse JSON", num_models=2)
    print("Code task models:")
    for m in code_models:
        print(f"  - {m.name} ({m.specialization.value})")

    # Creative task
    creative_models = selector.select_for_task("Write a creative short story", num_models=2)
    print("\nCreative task models:")
    for m in creative_models:
        print(f"  - {m.name} ({m.specialization.value})")

    # Get configuration
    config = selector.recommend_configuration(code_models)
    print(f"\nRecommended config: {config}")
