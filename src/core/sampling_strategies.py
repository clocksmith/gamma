"""
Sampling strategy templates for creative experimentation.

Provides pre-configured sampling strategies for different use cases:
- Creative writing
- Precise/factual generation
- Balanced generation
- Code generation
- Reasoning tasks
"""
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class SamplingStrategy:
    """A sampling strategy with pre-configured parameters."""
    name: str
    description: str
    temperature: float
    top_k: int
    top_p: float
    repetition_penalty: float = 1.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for engine use."""
        return {
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty
        }

    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  {self.description}\n"
            f"  temp={self.temperature}, top_k={self.top_k}, top_p={self.top_p}"
        )


# Pre-defined strategies

CREATIVE_WRITING = SamplingStrategy(
    name="Creative Writing",
    description="High temperature for diverse, creative outputs. Good for storytelling and brainstorming.",
    temperature=0.9,
    top_k=40,
    top_p=0.95,
    repetition_penalty=1.1,
    metadata={"use_cases": ["creative writing", "storytelling", "brainstorming", "poetry"]}
)

PRECISE_FACTUAL = SamplingStrategy(
    name="Precise & Factual",
    description="Low temperature for focused, deterministic outputs. Good for factual answers.",
    temperature=0.1,
    top_k=10,
    top_p=0.75,
    repetition_penalty=1.0,
    metadata={"use_cases": ["factual questions", "technical docs", "definitions"]}
)

BALANCED = SamplingStrategy(
    name="Balanced",
    description="Moderate settings for general-purpose use. Balance between creativity and focus.",
    temperature=0.7,
    top_k=50,
    top_p=0.9,
    repetition_penalty=1.05,
    metadata={"use_cases": ["general chat", "Q&A", "explanations"]}
)

CODE_GENERATION = SamplingStrategy(
    name="Code Generation",
    description="Settings optimized for generating syntactically correct code.",
    temperature=0.2,
    top_k=20,
    top_p=0.85,
    repetition_penalty=1.05,
    metadata={"use_cases": ["code generation", "code completion", "debugging"]}
)

REASONING = SamplingStrategy(
    name="Reasoning & Analysis",
    description="Lower temperature with broader top-k for step-by-step reasoning.",
    temperature=0.3,
    top_k=100,
    top_p=0.9,
    repetition_penalty=1.0,
    metadata={"use_cases": ["math problems", "logic puzzles", "analysis", "planning"]}
)

EXPLORATORY = SamplingStrategy(
    name="Exploratory",
    description="Very high temperature for maximum diversity. Experimental outputs.",
    temperature=1.5,
    top_k=100,
    top_p=0.98,
    repetition_penalty=1.15,
    metadata={"use_cases": ["creative exploration", "unexpected ideas", "surrealism"]}
)

CONSERVATIVE = SamplingStrategy(
    name="Conservative",
    description="Extremely low temperature for most predictable outputs. Near-greedy.",
    temperature=0.01,
    top_k=5,
    top_p=0.5,
    repetition_penalty=1.0,
    metadata={"use_cases": ["formal writing", "legal text", "medical documentation"]}
)


# Registry of all strategies
STRATEGY_REGISTRY: Dict[str, SamplingStrategy] = {
    "creative": CREATIVE_WRITING,
    "precise": PRECISE_FACTUAL,
    "balanced": BALANCED,
    "code": CODE_GENERATION,
    "reasoning": REASONING,
    "exploratory": EXPLORATORY,
    "conservative": CONSERVATIVE
}


def get_strategy(name: str) -> SamplingStrategy:
    """
    Get a sampling strategy by name.

    Args:
        name: Strategy name (e.g., "creative", "precise", "balanced")

    Returns:
        SamplingStrategy object

    Raises:
        KeyError: If strategy name not found
    """
    name_lower = name.lower()
    if name_lower not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise KeyError(
            f"Strategy '{name}' not found. Available: {available}"
        )
    return STRATEGY_REGISTRY[name_lower]


def list_strategies() -> List[SamplingStrategy]:
    """Get list of all available strategies."""
    return list(STRATEGY_REGISTRY.values())


def print_all_strategies():
    """Print all available strategies with descriptions."""
    print("\n" + "="*60)
    print("AVAILABLE SAMPLING STRATEGIES")
    print("="*60 + "\n")

    for strategy in list_strategies():
        print(strategy)
        print()


def create_custom_strategy(
    name: str,
    description: str,
    temperature: float,
    top_k: int,
    top_p: float,
    repetition_penalty: float = 1.0
) -> SamplingStrategy:
    """
    Create a custom sampling strategy.

    Args:
        name: Strategy name
        description: Strategy description
        temperature: Temperature value (0.0-2.0)
        top_k: Top-k value (0 = disabled)
        top_p: Top-p value (0.0-1.0)
        repetition_penalty: Repetition penalty (1.0 = no penalty)

    Returns:
        New SamplingStrategy object
    """
    # Validate parameters
    if not 0 <= temperature <= 2.0:
        raise ValueError("Temperature must be between 0 and 2.0")
    if not 0 <= top_p <= 1.0:
        raise ValueError("Top-p must be between 0 and 1.0")
    if top_k < 0:
        raise ValueError("Top-k must be >= 0")
    if repetition_penalty < 1.0:
        raise ValueError("Repetition penalty must be >= 1.0")

    return SamplingStrategy(
        name=name,
        description=description,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        metadata={"custom": True}
    )


def interpolate_strategies(
    strategy_a: SamplingStrategy,
    strategy_b: SamplingStrategy,
    alpha: float = 0.5
) -> SamplingStrategy:
    """
    Interpolate between two strategies.

    Args:
        strategy_a: First strategy
        strategy_b: Second strategy
        alpha: Interpolation factor (0.0 = all A, 1.0 = all B)

    Returns:
        New interpolated strategy
    """
    if not 0 <= alpha <= 1.0:
        raise ValueError("Alpha must be between 0 and 1.0")

    return SamplingStrategy(
        name=f"{strategy_a.name} → {strategy_b.name} ({alpha:.1f})",
        description=f"Interpolated between {strategy_a.name} and {strategy_b.name}",
        temperature=strategy_a.temperature * (1 - alpha) + strategy_b.temperature * alpha,
        top_k=int(strategy_a.top_k * (1 - alpha) + strategy_b.top_k * alpha),
        top_p=strategy_a.top_p * (1 - alpha) + strategy_b.top_p * alpha,
        repetition_penalty=strategy_a.repetition_penalty * (1 - alpha) + strategy_b.repetition_penalty * alpha,
        metadata={
            "interpolated": True,
            "source_a": strategy_a.name,
            "source_b": strategy_b.name,
            "alpha": alpha
        }
    )


def suggest_strategy_for_task(task_type: str) -> SamplingStrategy:
    """
    Suggest a sampling strategy for a given task type.

    Args:
        task_type: Type of task (e.g., "story", "code", "math", "chat")

    Returns:
        Recommended SamplingStrategy
    """
    task_lower = task_type.lower()

    task_mapping = {
        "story": CREATIVE_WRITING,
        "creative": CREATIVE_WRITING,
        "writing": CREATIVE_WRITING,
        "code": CODE_GENERATION,
        "programming": CODE_GENERATION,
        "debug": CODE_GENERATION,
        "math": REASONING,
        "logic": REASONING,
        "reasoning": REASONING,
        "analysis": REASONING,
        "fact": PRECISE_FACTUAL,
        "factual": PRECISE_FACTUAL,
        "definition": PRECISE_FACTUAL,
        "chat": BALANCED,
        "conversation": BALANCED,
        "qa": BALANCED,
    }

    for key, strategy in task_mapping.items():
        if key in task_lower:
            return strategy

    # Default to balanced
    return BALANCED


# Example usage and comparison
def compare_strategies(strategies: List[SamplingStrategy]):
    """
    Compare multiple strategies side-by-side.

    Args:
        strategies: List of strategies to compare
    """
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)

    headers = ["Strategy", "Temp", "Top-K", "Top-P", "Rep.Penalty"]
    col_widths = [30, 8, 8, 8, 12]

    # Print header
    header_row = ""
    for h, w in zip(headers, col_widths):
        header_row += f"{h:<{w}}"
    print(header_row)
    print("-" * 80)

    # Print each strategy
    for s in strategies:
        row = ""
        row += f"{s.name:<{col_widths[0]}}"
        row += f"{s.temperature:<{col_widths[1]}.2f}"
        row += f"{s.top_k:<{col_widths[2]}}"
        row += f"{s.top_p:<{col_widths[3]}.2f}"
        row += f"{s.repetition_penalty:<{col_widths[4]}.2f}"
        print(row)

    print("="*80 + "\n")
