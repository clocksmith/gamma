"""
Multi-LoRA Router for Mind Meld.

Enables dynamic per-token or per-turn adapter switching with minimal overhead.
Based on Activated LoRA (aLoRA) concepts - achieves 90% of ensemble versatility
at ~1% additional VRAM cost.

Key insight: Instead of loading multiple full models (2x VRAM), load one base model
and multiple tiny LoRA adapters (~8MB each). Route to appropriate adapter based on
content classification.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class AdapterDomain(Enum):
    """Pre-defined adapter domains for routing."""
    CODE = "code"
    MATH = "math"
    CREATIVE = "creative"
    FACTUAL = "factual"
    CONVERSATION = "conversation"
    TECHNICAL = "technical"
    GENERAL = "general"


@dataclass
class LoRAAdapter:
    """Represents a loaded LoRA adapter."""
    name: str
    path: str
    domain: AdapterDomain
    rank: int = 8
    alpha: float = 16.0
    size_bytes: int = 0
    loaded: bool = False
    weights: Optional[Any] = None  # Actual LoRA weights

    # Performance stats
    total_activations: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class RouterDecision:
    """Result from the router's decision."""
    selected_adapter: str
    confidence: float
    domain: AdapterDomain
    reasoning: str
    latency_ms: float


@dataclass
class MultiLoRAConfig:
    """Configuration for Multi-LoRA routing."""
    # Routing strategy
    routing_mode: str = "per_turn"  # "per_token", "per_turn", "per_sentence"

    # Classification thresholds
    code_keywords: List[str] = field(default_factory=lambda: [
        "def ", "class ", "import ", "function", "return ", "if ", "for ",
        "while ", "try:", "except", "async ", "await ", "=>", "const ",
        "let ", "var ", "public ", "private ", "void ", "int ", "string"
    ])
    math_keywords: List[str] = field(default_factory=lambda: [
        "calculate", "compute", "solve", "equation", "formula", "derivative",
        "integral", "probability", "statistics", "matrix", "vector", "sum",
        "product", "proof", "theorem", "=", "+", "-", "*", "/", "^"
    ])

    # Adapter switching
    min_confidence_for_switch: float = 0.6
    cooldown_tokens: int = 10  # Minimum tokens before switching again

    # Fallback behavior
    default_adapter: str = "general"
    fallback_on_low_confidence: bool = True


class ContentClassifierForLoRA:
    """
    Lightweight content classifier for LoRA routing.
    Uses keyword matching + simple heuristics (no ML model needed).
    """

    def __init__(self, config: MultiLoRAConfig):
        self.config = config
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile keyword patterns for fast matching."""
        self.code_set = set(kw.lower() for kw in self.config.code_keywords)
        self.math_set = set(kw.lower() for kw in self.config.math_keywords)

    def classify(self, text: str) -> Tuple[AdapterDomain, float]:
        """
        Classify text content to determine best adapter domain.

        Returns:
            (domain, confidence) tuple
        """
        text_lower = text.lower()

        # Count keyword matches
        code_score = sum(1 for kw in self.code_set if kw in text_lower)
        math_score = sum(1 for kw in self.math_set if kw in text_lower)

        # Normalize by keyword set sizes
        code_conf = min(code_score / 5, 1.0)  # 5 matches = max confidence
        math_conf = min(math_score / 4, 1.0)  # 4 matches = max confidence

        # Additional heuristics
        if "```" in text or text.strip().startswith(("def ", "class ", "function")):
            code_conf = max(code_conf, 0.8)

        if any(c in text for c in ["∫", "∑", "∏", "√", "π", "θ"]):
            math_conf = max(math_conf, 0.8)

        # Determine winner
        if code_conf > math_conf and code_conf >= self.config.min_confidence_for_switch:
            return AdapterDomain.CODE, code_conf
        elif math_conf > code_conf and math_conf >= self.config.min_confidence_for_switch:
            return AdapterDomain.MATH, math_conf
        elif "?" in text and len(text) < 200:
            return AdapterDomain.CONVERSATION, 0.5
        else:
            return AdapterDomain.GENERAL, 0.3


class MultiLoRARouter:
    """
    Routes inference to appropriate LoRA adapter based on content.

    Architecture:
    - Base model loaded once (e.g., Gemma 9B) - takes main VRAM
    - Multiple LoRA adapters loaded (~8MB each) - negligible VRAM
    - Router classifies content and activates appropriate adapter
    - Switching is nearly free (just pointer swap, no weight reload)

    This achieves "Multi-LoRA = 1.01x VRAM vs Mind Meld 2x VRAM"
    """

    def __init__(
        self,
        base_engine: Any,
        config: Optional[MultiLoRAConfig] = None,
        verbose: bool = False
    ):
        """
        Initialize Multi-LoRA Router.

        Args:
            base_engine: The base LLM engine (must support LoRA)
            config: Router configuration
            verbose: Enable verbose logging
        """
        self.base_engine = base_engine
        self.config = config or MultiLoRAConfig()
        self.verbose = verbose

        # Adapter registry
        self.adapters: Dict[str, LoRAAdapter] = {}
        self.active_adapter: Optional[str] = None

        # Classifier
        self.classifier = ContentClassifierForLoRA(self.config)

        # State tracking
        self.tokens_since_switch = 0
        self.switch_history: List[Tuple[int, str, str]] = []  # (token_idx, from, to)

        # Statistics
        self.total_routes = 0
        self.routes_by_domain: Dict[str, int] = {}

        logger.info("MultiLoRARouter initialized")

    def register_adapter(
        self,
        name: str,
        path: str,
        domain: AdapterDomain,
        rank: int = 8,
        alpha: float = 16.0
    ) -> bool:
        """
        Register a LoRA adapter for routing.

        Args:
            name: Unique identifier for the adapter
            path: Path to adapter weights
            domain: Content domain this adapter specializes in
            rank: LoRA rank (default 8)
            alpha: LoRA alpha scaling (default 16)

        Returns:
            True if registration successful
        """
        if name in self.adapters:
            logger.warning(f"Adapter '{name}' already registered, overwriting")

        adapter = LoRAAdapter(
            name=name,
            path=path,
            domain=domain,
            rank=rank,
            alpha=alpha
        )

        self.adapters[name] = adapter
        self.routes_by_domain[domain.value] = 0

        if self.verbose:
            logger.info(f"Registered adapter: {name} -> {domain.value}")

        return True

    def load_adapter(self, name: str) -> bool:
        """
        Load a specific adapter's weights into memory.

        For MLX, this uses mlx_lm's adapter loading.
        Adapters are small (~8MB) so loading is fast.
        """
        if name not in self.adapters:
            logger.error(f"Adapter '{name}' not registered")
            return False

        adapter = self.adapters[name]
        if adapter.loaded:
            return True

        try:
            # Check if engine supports adapter loading
            if hasattr(self.base_engine, '_load_adapter'):
                self.base_engine._load_adapter(adapter.path)
                adapter.loaded = True
                adapter.size_bytes = self._estimate_adapter_size(adapter.rank)
                logger.info(f"Loaded adapter '{name}' ({adapter.size_bytes / 1e6:.1f}MB)")
                return True
            else:
                # Fallback: store path for later use
                adapter.loaded = True
                logger.warning(f"Engine doesn't support dynamic adapter loading, storing path")
                return True
        except Exception as e:
            logger.error(f"Failed to load adapter '{name}': {e}")
            return False

    def _estimate_adapter_size(self, rank: int) -> int:
        """Estimate adapter size in bytes based on rank."""
        # Rough estimate: rank * hidden_dim * 2 (A and B matrices) * num_layers * 4 bytes
        # For 7B model with hidden_dim=4096, 32 layers:
        # rank=8: 8 * 4096 * 2 * 32 * 4 = ~8MB
        hidden_dim = 4096  # Approximate
        num_layers = 32
        return rank * hidden_dim * 2 * num_layers * 4

    def activate_adapter(self, name: str) -> bool:
        """
        Activate a specific adapter for inference.

        This is the fast path - just updates which LoRA weights are applied.
        No model reloading required.
        """
        if name not in self.adapters:
            if name == "none" or name is None:
                self.active_adapter = None
                return True
            logger.error(f"Adapter '{name}' not registered")
            return False

        adapter = self.adapters[name]

        if not adapter.loaded:
            if not self.load_adapter(name):
                return False

        old_adapter = self.active_adapter
        self.active_adapter = name

        # Update engine's active adapter if supported
        if hasattr(self.base_engine, '_set_active_adapter'):
            self.base_engine._set_active_adapter(adapter.path)

        if self.verbose and old_adapter != name:
            logger.info(f"Activated adapter: {old_adapter} -> {name}")

        return True

    def route(
        self,
        text: str,
        token_index: int = 0,
        force_domain: Optional[AdapterDomain] = None
    ) -> RouterDecision:
        """
        Route to appropriate adapter based on content.

        Args:
            text: Input text to classify
            token_index: Current token position (for cooldown)
            force_domain: Override classification with specific domain

        Returns:
            RouterDecision with selected adapter and confidence
        """
        start_time = time.time()

        # Check cooldown
        if self.tokens_since_switch < self.config.cooldown_tokens:
            # Stay with current adapter
            current = self.active_adapter or self.config.default_adapter
            return RouterDecision(
                selected_adapter=current,
                confidence=1.0,
                domain=self.adapters.get(current, LoRAAdapter(
                    name=current, path="", domain=AdapterDomain.GENERAL
                )).domain,
                reasoning="Cooldown period - maintaining current adapter",
                latency_ms=(time.time() - start_time) * 1000
            )

        # Classify content
        if force_domain:
            domain = force_domain
            confidence = 1.0
        else:
            domain, confidence = self.classifier.classify(text)

        # Find best adapter for domain
        selected = self._find_adapter_for_domain(domain)

        # Apply confidence threshold
        if confidence < self.config.min_confidence_for_switch:
            if self.config.fallback_on_low_confidence:
                selected = self.config.default_adapter
                domain = AdapterDomain.GENERAL

        # Track switch
        old_adapter = self.active_adapter
        if selected != old_adapter:
            self.switch_history.append((token_index, old_adapter or "none", selected))
            self.tokens_since_switch = 0
        else:
            self.tokens_since_switch += 1

        # Activate selected adapter
        self.activate_adapter(selected)

        # Update stats
        self.total_routes += 1
        self.routes_by_domain[domain.value] = self.routes_by_domain.get(domain.value, 0) + 1

        latency = (time.time() - start_time) * 1000

        return RouterDecision(
            selected_adapter=selected,
            confidence=confidence,
            domain=domain,
            reasoning=f"Classified as {domain.value} with {confidence:.2f} confidence",
            latency_ms=latency
        )

    def _find_adapter_for_domain(self, domain: AdapterDomain) -> str:
        """Find the best registered adapter for a domain."""
        # First, look for exact match
        for name, adapter in self.adapters.items():
            if adapter.domain == domain:
                return name

        # Fallback to default
        return self.config.default_adapter

    def route_and_generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route to adapter and generate response.

        For per_turn mode, classifies once at the start.
        For per_token mode, reclassifies periodically.
        """
        # Initial routing
        decision = self.route(prompt, token_index=0)

        if self.verbose:
            logger.info(f"Initial route: {decision.selected_adapter} ({decision.reasoning})")

        # Generate using base engine with active adapter
        generated_tokens = []
        current_text = prompt

        for i in range(max_tokens):
            # Per-token routing (if enabled)
            if self.config.routing_mode == "per_token" and i > 0:
                decision = self.route(current_text, token_index=i)

            # Generate next token
            input_ids, attention_mask = self.base_engine.encode(current_text, add_special_tokens=True)
            result = self.base_engine.predict_next(
                input_ids, attention_mask,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p
            )

            token_id = result['next_token_id']
            token_text = self.base_engine.decode([token_id], skip_special_tokens=False)

            generated_tokens.append(token_id)
            current_text += token_text

            # Check for EOS
            if token_id == self.base_engine.get_eos_token_id():
                break

            # Per-sentence routing
            if self.config.routing_mode == "per_sentence":
                if token_text.strip() in [".", "!", "?", "\n"]:
                    decision = self.route(current_text, token_index=i)

        # Compile stats
        stats = {
            'total_tokens': len(generated_tokens),
            'adapter_used': self.active_adapter,
            'switches': len(self.switch_history),
            'switch_history': self.switch_history[-10:],  # Last 10 switches
            'routes_by_domain': self.routes_by_domain.copy()
        }

        return current_text[len(prompt):], stats

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            'total_routes': self.total_routes,
            'routes_by_domain': self.routes_by_domain,
            'active_adapter': self.active_adapter,
            'registered_adapters': list(self.adapters.keys()),
            'loaded_adapters': [n for n, a in self.adapters.items() if a.loaded],
            'total_switches': len(self.switch_history),
            'adapter_stats': {
                name: {
                    'domain': a.domain.value,
                    'activations': a.total_activations,
                    'size_mb': a.size_bytes / 1e6
                }
                for name, a in self.adapters.items()
            }
        }


class MultiLoRAMeldEngine:
    """
    Mind Meld engine using Multi-LoRA routing instead of multiple models.

    Provides the versatility of model ensembles at fraction of the cost:
    - Single base model in VRAM
    - Multiple tiny LoRA adapters (~8MB each)
    - Dynamic routing based on content

    Memory comparison:
    - Traditional ensemble (2x 9B): ~40GB VRAM
    - Multi-LoRA (1x 9B + 4 LoRAs): ~20GB + 32MB = ~20GB VRAM
    """

    def __init__(
        self,
        base_engine: Any,
        adapter_configs: List[Dict[str, Any]],
        config: Optional[MultiLoRAConfig] = None,
        verbose: bool = False
    ):
        """
        Initialize Multi-LoRA Meld Engine.

        Args:
            base_engine: Base LLM engine
            adapter_configs: List of adapter configurations:
                [{'name': 'code', 'path': '/path/to/lora', 'domain': 'code'}, ...]
            config: Router configuration
            verbose: Enable verbose logging
        """
        self.router = MultiLoRARouter(base_engine, config, verbose)
        self.verbose = verbose

        # Register all adapters
        for ac in adapter_configs:
            domain = AdapterDomain(ac.get('domain', 'general'))
            self.router.register_adapter(
                name=ac['name'],
                path=ac['path'],
                domain=domain,
                rank=ac.get('rank', 8),
                alpha=ac.get('alpha', 16.0)
            )

        logger.info(f"MultiLoRAMeldEngine initialized with {len(adapter_configs)} adapters")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate using routed LoRA adapter."""
        return self.router.route_and_generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    def get_memory_usage(self) -> Dict[str, Any]:
        """Estimate memory usage comparison."""
        base_size_gb = 20.0  # Approximate 9B model at 4-bit
        adapter_size_mb = sum(
            a.size_bytes / 1e6 for a in self.router.adapters.values()
        )

        return {
            'base_model_gb': base_size_gb,
            'adapters_mb': adapter_size_mb,
            'total_gb': base_size_gb + adapter_size_mb / 1000,
            'equivalent_ensemble_gb': base_size_gb * len(self.router.adapters),
            'savings_percent': (1 - (base_size_gb + adapter_size_mb / 1000) /
                               (base_size_gb * max(len(self.router.adapters), 1))) * 100
        }
