"""Statistics tracking for Mind Meld mode"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import numpy as np


@dataclass
class ModelStatistics:
    """Statistics for a single model"""
    model_name: str
    tokens_generated: int = 0
    total_time: float = 0.0
    avg_confidence: float = 0.0
    avg_perplexity: float = 0.0
    swap_count: int = 0
    consecutive_tokens: List[int] = field(default_factory=list)
    confidence_history: List[float] = field(default_factory=list)
    perplexity_history: List[float] = field(default_factory=list)
    token_texts: List[str] = field(default_factory=list)
    
    @property
    def avg_time_per_token(self) -> float:
        """Average time per token"""
        return self.total_time / self.tokens_generated if self.tokens_generated > 0 else 0.0
    
    @property
    def contribution_percentage(self) -> float:
        """Percentage contribution (set by MeldStatistics)"""
        return getattr(self, '_contribution_pct', 0.0)
    
    def update(self, token_text: str, confidence: float, time_taken: float, perplexity: Optional[float] = None):
        """Update statistics with new token"""
        self.tokens_generated += 1
        self.total_time += time_taken
        self.token_texts.append(token_text)
        self.confidence_history.append(confidence)
        
        if perplexity is not None:
            self.perplexity_history.append(perplexity)
            self.avg_perplexity = np.mean(self.perplexity_history)
        
        self.avg_confidence = np.mean(self.confidence_history)


@dataclass
class SwapEvent:
    """Record of a model swap event"""
    round_num: int
    from_model: str
    to_model: str
    reason: str
    token_before: str
    timestamp: float


@dataclass
class MeldStatistics:
    """Complete statistics for a Mind Meld session"""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_tokens: int = 0
    total_swaps: int = 0
    model_stats: Dict[str, ModelStatistics] = field(default_factory=dict)
    swap_events: List[SwapEvent] = field(default_factory=list)
    swap_patterns: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    current_streak: int = 0
    current_model: Optional[str] = None
    max_streak: Tuple[str, int] = ("", 0)
    
    @property
    def duration(self) -> float:
        """Total duration of the session"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def swaps_per_token(self) -> float:
        """Average swaps per token"""
        return self.total_swaps / self.total_tokens if self.total_tokens > 0 else 0.0
    
    def add_model(self, model_name: str):
        """Add a model to track"""
        if model_name not in self.model_stats:
            self.model_stats[model_name] = ModelStatistics(model_name)
    
    def record_token(
        self,
        model_name: str,
        token_text: str,
        confidence: float,
        time_taken: float,
        perplexity: Optional[float] = None
    ):
        """Record a token generation"""
        self.total_tokens += 1
        
        if model_name not in self.model_stats:
            self.add_model(model_name)
        
        self.model_stats[model_name].update(token_text, confidence, time_taken, perplexity)
        
        # Update streak tracking
        if self.current_model == model_name:
            self.current_streak += 1
        else:
            if self.current_model and self.current_streak > self.max_streak[1]:
                self.max_streak = (self.current_model, self.current_streak)
            self.current_model = model_name
            self.current_streak = 1
        
        # Track consecutive tokens
        self.model_stats[model_name].consecutive_tokens.append(self.current_streak)
    
    def record_swap(
        self,
        round_num: int,
        from_model: str,
        to_model: str,
        reason: str,
        token_before: str
    ):
        """Record a model swap"""
        self.total_swaps += 1
        
        swap = SwapEvent(
            round_num=round_num,
            from_model=from_model,
            to_model=to_model,
            reason=reason,
            token_before=token_before,
            timestamp=time.time()
        )
        self.swap_events.append(swap)
        
        # Track swap patterns
        pattern_key = f"{from_model} -> {to_model}"
        self.swap_patterns[pattern_key] += 1
        
        # Update model swap counts
        if from_model in self.model_stats:
            self.model_stats[from_model].swap_count += 1
    
    def calculate_contributions(self):
        """Calculate contribution percentages for each model"""
        if self.total_tokens == 0:
            return
        
        for model_name, stats in self.model_stats.items():
            stats._contribution_pct = (stats.tokens_generated / self.total_tokens) * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of statistics"""
        self.calculate_contributions()
        
        summary = {
            "duration_seconds": self.duration,
            "total_tokens": self.total_tokens,
            "total_swaps": self.total_swaps,
            "swaps_per_token": self.swaps_per_token,
            "max_streak": {
                "model": self.max_streak[0],
                "length": self.max_streak[1]
            },
            "models": {}
        }
        
        for model_name, stats in self.model_stats.items():
            summary["models"][model_name] = {
                "tokens_generated": stats.tokens_generated,
                "contribution_pct": f"{stats.contribution_percentage:.1f}%",
                "avg_confidence": f"{stats.avg_confidence:.3f}",
                "avg_time_per_token": f"{stats.avg_time_per_token:.3f}s",
                "swap_count": stats.swap_count
            }
            if stats.avg_perplexity > 0:
                summary["models"][model_name]["avg_perplexity"] = f"{stats.avg_perplexity:.2f}"
        
        # Add swap patterns
        if self.swap_patterns:
            summary["top_swap_patterns"] = dict(
                sorted(self.swap_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
            )
        
        return summary
    
    def print_summary(self):
        """Print a formatted summary"""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("Mind Meld Session Statistics")
        print("="*70)
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"  Total tokens: {summary['total_tokens']}")
        print(f"  Total swaps: {summary['total_swaps']}")
        print(f"  Swaps per token: {summary['swaps_per_token']:.2f}")
        print(f"  Longest streak: {summary['max_streak']['model']} ({summary['max_streak']['length']} tokens)")
        
        print(f"\n📈 Model Contributions:")
        for model_name, model_summary in summary['models'].items():
            print(f"\n  {model_name}:")
            print(f"    Tokens: {model_summary['tokens_generated']} ({model_summary['contribution_pct']})")
            print(f"    Avg confidence: {model_summary['avg_confidence']}")
            print(f"    Avg time/token: {model_summary['avg_time_per_token']}")
            print(f"    Swaps from this model: {model_summary['swap_count']}")
            if 'avg_perplexity' in model_summary:
                print(f"    Avg perplexity: {model_summary['avg_perplexity']}")
        
        if 'top_swap_patterns' in summary and summary['top_swap_patterns']:
            print(f"\n🔄 Top Swap Patterns:")
            for pattern, count in summary['top_swap_patterns'].items():
                print(f"  {pattern}: {count} times")
        
        print("="*70)
    
    def print_live_stats(self, current_model: str, round_num: int):
        """Print live statistics during generation"""
        self.calculate_contributions()
        
        # Create a simple progress bar for model contributions
        bar_width = 40
        contributions = []
        
        for model_name, stats in self.model_stats.items():
            pct = stats.contribution_percentage / 100
            filled = int(bar_width * pct)
            bar = "█" * filled + "░" * (bar_width - filled)
            contributions.append(f"  {model_name:20} [{bar}] {stats.contribution_percentage:.1f}%")
        
        print(f"\n📊 Round {round_num} | Active: {current_model}")
        print("Model Contributions:")
        for contrib in contributions:
            print(contrib)
        print(f"Swaps: {self.total_swaps} | Tokens: {self.total_tokens} | Ratio: {self.swaps_per_token:.2f}")
    
    def save_to_file(self, filepath: str):
        """Save statistics to JSON file"""
        self.calculate_contributions()
        
        # Convert to serializable format
        data = {
            "summary": self.get_summary(),
            "detailed": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "total_tokens": self.total_tokens,
                "total_swaps": self.total_swaps,
                "swap_events": [asdict(event) for event in self.swap_events],
                "swap_patterns": dict(self.swap_patterns),
                "models": {}
            }
        }
        
        for model_name, stats in self.model_stats.items():
            data["detailed"]["models"][model_name] = {
                "tokens_generated": stats.tokens_generated,
                "total_time": stats.total_time,
                "avg_confidence": stats.avg_confidence,
                "avg_perplexity": stats.avg_perplexity,
                "swap_count": stats.swap_count,
                "token_texts": stats.token_texts[:100],  # Limit to first 100 tokens
                "confidence_history": stats.confidence_history[:100],
                "consecutive_tokens": stats.consecutive_tokens[:100]
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n📁 Statistics saved to: {filepath}")


class StatisticsTracker:
    """Convenience class for tracking statistics in Mind Meld"""
    
    def __init__(self, models: List[str], show_live: bool = False, save_file: Optional[str] = None):
        self.stats = MeldStatistics()
        self.show_live = show_live
        self.save_file = save_file
        self.round_counter = 0
        
        # Initialize models
        for model in models:
            self.stats.add_model(model)
    
    def start_round(self) -> int:
        """Start a new round"""
        self.round_counter += 1
        return self.round_counter
    
    def record_token(
        self,
        model_name: str,
        token_text: str,
        confidence: float = 1.0,
        time_taken: float = 0.0,
        perplexity: Optional[float] = None
    ):
        """Record a token generation"""
        self.stats.record_token(model_name, token_text, confidence, time_taken, perplexity)
        
        if self.show_live and self.round_counter % 5 == 0:  # Show every 5 rounds
            self.stats.print_live_stats(model_name, self.round_counter)
    
    def record_swap(
        self,
        from_model: str,
        to_model: str,
        reason: str,
        token_before: str
    ):
        """Record a model swap"""
        self.stats.record_swap(self.round_counter, from_model, to_model, reason, token_before)
    
    def finish(self):
        """Finish tracking and show/save results"""
        self.stats.end_time = time.time()
        self.stats.print_summary()
        
        if self.save_file:
            self.stats.save_to_file(self.save_file)