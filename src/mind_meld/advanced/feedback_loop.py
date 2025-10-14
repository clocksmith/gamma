"""
Feedback Loop System for Mind Meld.

Enables self-critique and iterative refinement of generated content.
One model generates, another critiques, generator refines based on feedback.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.core.engine_interface import LLMEngine


class FeedbackType(Enum):
    """Types of feedback."""
    GRAMMAR = "grammar"
    COHERENCE = "coherence"
    FACTUALITY = "factuality"
    STYLE = "style"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"


@dataclass
class Feedback:
    """Feedback from critic model."""
    feedback_type: FeedbackType
    score: float  # 0-1, higher is better
    comments: str
    suggestions: List[str]
    needs_revision: bool


@dataclass
class FeedbackResult:
    """Result of feedback loop iteration."""
    original_text: str
    revised_text: str
    feedbacks: List[Feedback]
    num_iterations: int
    improvement_score: float
    converged: bool


class FeedbackLoop:
    """
    Self-critique and refinement system.

    Generator creates content, Critic evaluates it, Generator refines.
    """

    def __init__(
        self,
        generator_model: LLMEngine,
        critic_model: LLMEngine,
        max_iterations: int = 3,
        min_score_threshold: float = 0.8,
        verbose: bool = False
    ):
        """
        Initialize feedback loop.

        Args:
            generator_model: Model that generates content
            critic_model: Model that critiques content
            max_iterations: Maximum refinement iterations
            min_score_threshold: Minimum quality score to accept
            verbose: Enable verbose logging
        """
        self.generator = generator_model
        self.critic = critic_model
        self.max_iterations = max_iterations
        self.min_score_threshold = min_score_threshold
        self.verbose = verbose

        # Statistics
        self.total_iterations = 0
        self.total_refinements = 0
        self.avg_improvement = 0.0

    def _log(self, message: str):
        """Log if verbose."""
        if self.verbose:
            print(f"[FeedbackLoop] {message}")

    def generate_initial(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7
    ) -> str:
        """
        Generate initial content.

        Args:
            prompt: Generation prompt
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        self._log("Generating initial content...")

        generated = prompt

        for _ in range(max_tokens):
            input_ids, attention_mask = self.generator.encode(generated, add_special_tokens=True)
            result = self.generator.predict_next(
                input_ids,
                attention_mask,
                temperature=temperature,
                top_k=50,
                top_p=0.95
            )

            token_id = result['next_token_id']
            token_text = self.generator.get_token_text(token_id)
            generated += token_text

            if token_id == self.generator.get_eos_token_id():
                break

        self._log(f"Generated {len(generated) - len(prompt)} chars")
        return generated

    def critique(self, text: str, aspect: FeedbackType) -> Feedback:
        """
        Generate critique for text on specific aspect.

        Args:
            text: Text to critique
            aspect: Aspect to evaluate

        Returns:
            Feedback object
        """
        critique_prompt = self._build_critique_prompt(text, aspect)

        # Generate critique
        input_ids, attention_mask = self.critic.encode(critique_prompt, add_special_tokens=True)
        result = self.critic.predict_next(
            input_ids,
            attention_mask,
            temperature=0.3,  # Lower temp for more focused critique
            top_k=50,
            top_p=0.95
        )

        # Parse critique (simplified - in practice, would generate full critique)
        # For now, use a heuristic based on text quality indicators
        score = self._estimate_quality_score(text, aspect)
        needs_revision = score < self.min_score_threshold

        comments = f"Quality score: {score:.2f} for {aspect.value}"
        suggestions = self._generate_suggestions(text, aspect, score)

        return Feedback(
            feedback_type=aspect,
            score=score,
            comments=comments,
            suggestions=suggestions,
            needs_revision=needs_revision
        )

    def _build_critique_prompt(self, text: str, aspect: FeedbackType) -> str:
        """Build prompt for critique generation."""
        aspect_instructions = {
            FeedbackType.GRAMMAR: "Check for grammatical errors, spelling mistakes, and punctuation issues.",
            FeedbackType.COHERENCE: "Evaluate logical flow and coherence of ideas.",
            FeedbackType.FACTUALITY: "Verify factual accuracy and identify potential inaccuracies.",
            FeedbackType.STYLE: "Assess writing style, tone, and appropriateness.",
            FeedbackType.COMPLETENESS: "Check if the text adequately addresses the topic.",
            FeedbackType.RELEVANCE: "Evaluate relevance to the intended purpose."
        }

        instruction = aspect_instructions.get(aspect, "Evaluate the text quality.")

        return f"""Critique the following text for {aspect.value}.

{instruction}

Text:
{text}

Provide a constructive critique:"""

    def _estimate_quality_score(self, text: str, aspect: FeedbackType) -> float:
        """
        Estimate quality score using heuristics.

        In a full implementation, this would use the critic model's output.
        """
        score = 0.5  # Base score

        # Length check
        if len(text.strip()) < 10:
            score -= 0.3
        elif len(text.strip()) > 50:
            score += 0.1

        # Grammar heuristics
        if aspect == FeedbackType.GRAMMAR:
            # Check for basic indicators
            sentences = text.split('.')
            if any(len(s.strip()) > 0 and s.strip()[0].islower() for s in sentences[1:]):
                score -= 0.1  # Capitalization issues

            # Check for reasonable sentence length
            avg_sentence_len = np.mean([len(s.split()) for s in sentences if s.strip()])
            if 5 <= avg_sentence_len <= 30:
                score += 0.2

        # Coherence heuristics
        elif aspect == FeedbackType.COHERENCE:
            # Check for discourse markers
            markers = ['however', 'therefore', 'moreover', 'furthermore', 'additionally']
            if any(marker in text.lower() for marker in markers):
                score += 0.2

        # Style heuristics
        elif aspect == FeedbackType.STYLE:
            # Check for varied sentence structure
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if len(set(len(s.split()) for s in sentences)) > 1:
                score += 0.2

        return np.clip(score, 0.0, 1.0)

    def _generate_suggestions(
        self,
        text: str,
        aspect: FeedbackType,
        score: float
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        if score < 0.5:
            if aspect == FeedbackType.GRAMMAR:
                suggestions.append("Check spelling and punctuation")
                suggestions.append("Ensure proper capitalization")
            elif aspect == FeedbackType.COHERENCE:
                suggestions.append("Add transitional phrases between ideas")
                suggestions.append("Ensure logical progression of thoughts")
            elif aspect == FeedbackType.STYLE:
                suggestions.append("Vary sentence structure")
                suggestions.append("Consider tone and audience")

        return suggestions

    def refine(
        self,
        original_text: str,
        feedbacks: List[Feedback],
        temperature: float = 0.5
    ) -> str:
        """
        Refine text based on feedback.

        Args:
            original_text: Original text
            feedbacks: List of feedback to incorporate
            temperature: Sampling temperature

        Returns:
            Refined text
        """
        # Build refinement prompt
        refinement_prompt = self._build_refinement_prompt(original_text, feedbacks)

        self._log("Refining based on feedback...")

        # Generate refinement
        refined = ""
        for _ in range(len(original_text) * 2):  # Allow up to 2x original length
            input_ids, attention_mask = self.generator.encode(
                refinement_prompt + refined,
                add_special_tokens=True
            )
            result = self.generator.predict_next(
                input_ids,
                attention_mask,
                temperature=temperature,
                top_k=50,
                top_p=0.95
            )

            token_id = result['next_token_id']
            token_text = self.generator.get_token_text(token_id)
            refined += token_text

            if token_id == self.generator.get_eos_token_id():
                break

        self.total_refinements += 1
        return refined.strip()

    def _build_refinement_prompt(self, text: str, feedbacks: List[Feedback]) -> str:
        """Build prompt for refinement."""
        feedback_summary = "\n".join([
            f"- {fb.feedback_type.value}: {fb.comments} (Score: {fb.score:.2f})"
            for fb in feedbacks
        ])

        suggestions = []
        for fb in feedbacks:
            suggestions.extend(fb.suggestions)

        suggestions_text = "\n".join([f"- {s}" for s in suggestions[:5]])  # Top 5

        return f"""Revise the following text based on the feedback provided.

Original text:
{text}

Feedback:
{feedback_summary}

Suggestions:
{suggestions_text}

Revised text:"""

    def run_loop(
        self,
        prompt: str,
        max_tokens: int = 100,
        aspects: Optional[List[FeedbackType]] = None,
        temperature: float = 0.7
    ) -> FeedbackResult:
        """
        Run complete feedback loop.

        Args:
            prompt: Initial prompt
            max_tokens: Max tokens for initial generation
            aspects: Aspects to evaluate (defaults to all)
            temperature: Generation temperature

        Returns:
            FeedbackResult with final output and statistics
        """
        if aspects is None:
            aspects = [FeedbackType.GRAMMAR, FeedbackType.COHERENCE, FeedbackType.STYLE]

        # Initial generation
        current_text = self.generate_initial(prompt, max_tokens, temperature)
        original_text = current_text

        iteration = 0
        converged = False
        all_feedbacks = []

        while iteration < self.max_iterations and not converged:
            iteration += 1
            self.total_iterations += 1

            self._log(f"Iteration {iteration}/{self.max_iterations}")

            # Critique current text
            iter_feedbacks = []
            for aspect in aspects:
                feedback = self.critique(current_text, aspect)
                iter_feedbacks.append(feedback)
                all_feedbacks.append(feedback)

                self._log(f"  {aspect.value}: {feedback.score:.2f}")

            # Check if refinement needed
            needs_refinement = any(fb.needs_revision for fb in iter_feedbacks)
            avg_score = np.mean([fb.score for fb in iter_feedbacks])

            if not needs_refinement or avg_score >= self.min_score_threshold:
                self._log(f"Converged with score {avg_score:.2f}")
                converged = True
                break

            # Refine
            current_text = self.refine(current_text, iter_feedbacks, temperature)

        # Calculate improvement
        initial_scores = [fb.score for fb in all_feedbacks[:len(aspects)]]
        final_scores = [fb.score for fb in all_feedbacks[-len(aspects):]]

        improvement = np.mean(final_scores) - np.mean(initial_scores)
        self.avg_improvement = (
            self.avg_improvement * (self.total_refinements - 1) + improvement
        ) / self.total_refinements

        return FeedbackResult(
            original_text=original_text,
            revised_text=current_text,
            feedbacks=all_feedbacks,
            num_iterations=iteration,
            improvement_score=improvement,
            converged=converged
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get feedback loop statistics."""
        return {
            'total_iterations': self.total_iterations,
            'total_refinements': self.total_refinements,
            'avg_improvement': self.avg_improvement,
            'max_iterations': self.max_iterations,
            'min_score_threshold': self.min_score_threshold
        }
