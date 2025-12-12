"""
Adversarial Dynamics for Mind Meld.

Red team generates claims, Blue team challenges them.
Produces robust, fact-checked output through debate.
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

from src.core.engine_interface import LLMEngine
from src.mind_meld.utils import VerboseLoggerMixin


@dataclass
class Claim:
    """A claim made by red team."""
    text: str
    confidence: float
    supporting_evidence: List[str]


@dataclass
class Challenge:
    """A challenge from blue team."""
    claim: Claim
    challenge_text: str
    counter_evidence: List[str]
    strength: float  # 0-1


@dataclass
class DebateResult:
    """Result of adversarial debate."""
    original_claim: Claim
    challenges: List[Challenge]
    final_consensus: str
    confidence_score: float
    rounds: int


class AdversarialDebate(VerboseLoggerMixin):
    """
    Adversarial debate between red and blue teams.

    Red team proposes, Blue team challenges, iterate to consensus.
    """

    def __init__(
        self,
        red_team: LLMEngine,
        blue_team: LLMEngine,
        max_rounds: int = 3,
        verbose: bool = False
    ):
        """
        Initialize adversarial debate.

        Args:
            red_team: Model that generates claims
            blue_team: Model that challenges claims
            max_rounds: Maximum debate rounds
            verbose: Enable verbose logging
        """
        self.red_team = red_team
        self.blue_team = blue_team
        self.max_rounds = max_rounds
        self.verbose = verbose

    def generate_claim(self, topic: str, temperature: float = 0.7) -> Claim:
        """Generate initial claim from red team."""
        self._log(f"Red team generating claim about: {topic}")

        claim_prompt = f"""Make a clear, specific claim about the following topic:

Topic: {topic}

Claim:"""

        # Generate claim
        generated = ""
        for _ in range(100):
            input_ids, attention_mask = self.red_team.encode(
                claim_prompt + generated,
                add_special_tokens=True
            )
            result = self.red_team.predict_next(
                input_ids,
                attention_mask,
                temperature=temperature,
                top_k=50,
                top_p=0.95
            )

            token_id = result['next_token_id']
            token_text = self.red_team.get_token_text(token_id)
            generated += token_text

            if token_id == self.red_team.get_eos_token_id() or '\n' in generated:
                break

        claim_text = generated.strip()

        # Estimate confidence (simplified)
        confidence = 0.8  # Would analyze model probabilities

        return Claim(
            text=claim_text,
            confidence=confidence,
            supporting_evidence=[]
        )

    def challenge_claim(
        self,
        claim: Claim,
        temperature: float = 0.5
    ) -> Challenge:
        """Generate challenge from blue team."""
        self._log("Blue team challenging claim...")

        challenge_prompt = f"""Critically evaluate the following claim. Identify potential issues, counter-arguments, or request clarification.

Claim: {claim.text}

Challenge:"""

        # Generate challenge
        generated = ""
        for _ in range(150):
            input_ids, attention_mask = self.blue_team.encode(
                challenge_prompt + generated,
                add_special_tokens=True
            )
            result = self.blue_team.predict_next(
                input_ids,
                attention_mask,
                temperature=temperature,
                top_k=50,
                top_p=0.95
            )

            token_id = result['next_token_id']
            token_text = self.blue_team.get_token_text(token_id)
            generated += token_text

            if token_id == self.blue_team.get_eos_token_id():
                break

        challenge_text = generated.strip()

        # Estimate challenge strength
        strength = 0.7  # Would analyze actual challenge quality

        return Challenge(
            claim=claim,
            challenge_text=challenge_text,
            counter_evidence=[],
            strength=strength
        )

    def synthesize_consensus(
        self,
        claim: Claim,
        challenges: List[Challenge],
        temperature: float = 0.5
    ) -> Tuple[str, float]:
        """
        Synthesize consensus from debate.

        Args:
            claim: Original claim
            challenges: List of challenges
            temperature: Sampling temperature

        Returns:
            (consensus_text, confidence_score)
        """
        self._log("Synthesizing consensus...")

        # Build synthesis prompt
        challenges_text = "\n".join([
            f"- {c.challenge_text}"
            for c in challenges
        ])

        synthesis_prompt = f"""Given the following claim and challenges, synthesize a balanced, well-supported conclusion.

Original Claim: {claim.text}

Challenges:
{challenges_text}

Synthesized Conclusion:"""

        # Generate consensus
        generated = ""
        for _ in range(200):
            input_ids, attention_mask = self.red_team.encode(
                synthesis_prompt + generated,
                add_special_tokens=True
            )
            result = self.red_team.predict_next(
                input_ids,
                attention_mask,
                temperature=temperature,
                top_k=50,
                top_p=0.95
            )

            token_id = result['next_token_id']
            token_text = self.red_team.get_token_text(token_id)
            generated += token_text

            if token_id == self.red_team.get_eos_token_id():
                break

        consensus = generated.strip()

        # Calculate confidence based on challenges
        avg_challenge_strength = sum(c.strength for c in challenges) / len(challenges) if challenges else 0
        confidence = claim.confidence * (1 - 0.3 * avg_challenge_strength)

        return consensus, confidence

    def debate(
        self,
        topic: str,
        temperature: float = 0.7
    ) -> DebateResult:
        """
        Run complete adversarial debate.

        Args:
            topic: Topic to debate
            temperature: Sampling temperature

        Returns:
            DebateResult with consensus
        """
        # Generate initial claim
        claim = self.generate_claim(topic, temperature)

        challenges = []
        rounds = 0

        # Iterative challenge-response
        for round_num in range(self.max_rounds):
            rounds += 1
            self._log(f"Debate round {round_num + 1}/{self.max_rounds}")

            # Blue team challenges
            challenge = self.challenge_claim(claim, temperature * 0.8)
            challenges.append(challenge)

            # Check if challenges are strong enough to continue
            if challenge.strength < 0.5:
                self._log("Challenges weakening, reaching consensus")
                break

        # Synthesize final consensus
        consensus, confidence = self.synthesize_consensus(
            claim,
            challenges,
            temperature * 0.6
        )

        return DebateResult(
            original_claim=claim,
            challenges=challenges,
            final_consensus=consensus,
            confidence_score=confidence,
            rounds=rounds
        )

    def generate_with_debate(
        self,
        topic: str,
        temperature: float = 0.7
    ) -> Tuple[str, DebateResult]:
        """
        Generate text through adversarial debate.

        Args:
            topic: Topic to explore
            temperature: Sampling temperature

        Returns:
            (final_text, debate_result)
        """
        result = self.debate(topic, temperature)
        return result.final_consensus, result
