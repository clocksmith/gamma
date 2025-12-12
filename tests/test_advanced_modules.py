"""Tests for Mind Meld advanced modules."""

import unittest
import numpy as np
from unittest.mock import MagicMock, patch

# MoE Router
from src.mind_meld.advanced.moe_router import (
    ContentType, ContentClassifier, MoERouter, AdaptiveMoERouter
)

# Speculative Decoding
from src.mind_meld.advanced.speculative_decoding import (
    SpeculativeResult, SpeculativeDecoder, SpeculativeMeldEngine
)

# Contrastive Decoding
from src.mind_meld.advanced.contrastive_decoding import (
    ContrastiveConfig, ContrastiveDecoder, MultiModelContrastiveDecoder
)

# Feedback Loop
from src.mind_meld.advanced.feedback_loop import (
    FeedbackType, Feedback, FeedbackResult, FeedbackLoop
)

# Hierarchical Control
from src.mind_meld.advanced.hierarchical_control import (
    PlanStep, ExecutionPlan, ExecutionResult, HierarchicalController
)

# Adversarial
from src.mind_meld.advanced.adversarial import (
    Claim, Challenge, DebateResult, AdversarialDebate
)


def create_mock_engine(name: str = "mock", vocab_size: int = 100):
    """Create a mock LLM engine for testing."""
    engine = MagicMock()
    engine.model_name = name
    engine.encode.return_value = (np.array([1, 2, 3]), np.array([1, 1, 1]))
    engine.predict_next.return_value = {
        'next_token_id': 5,
        'logits_raw': np.random.randn(vocab_size),
        'probability': 0.5
    }
    engine.get_token_text.return_value = " token"
    engine.decode.return_value = " token"
    engine.get_eos_token_id.return_value = 0
    engine.convert_to_numpy.side_effect = lambda x: np.array(x) if not isinstance(x, np.ndarray) else x
    return engine


# =============================================================================
# Content Classifier Tests
# =============================================================================
class TestContentClassifier(unittest.TestCase):
    """Tests for ContentClassifier."""

    def setUp(self):
        self.classifier = ContentClassifier(verbose=False)

    def test_classify_code_context(self):
        """Should classify code-like content as CODE."""
        context = "def hello_world():\n    print('Hello')\n    return True"
        result = self.classifier.classify_context(context)
        self.assertEqual(result, ContentType.CODE)

    def test_classify_math_context(self):
        """Should classify math-like content as MATH."""
        context = "The equation to solve is: x^2 + 5x + 6 = 0. Calculate the derivative."
        result = self.classifier.classify_context(context)
        self.assertEqual(result, ContentType.MATH)

    def test_classify_creative_context(self):
        """Should classify creative content correctly."""
        context = "The story begins with a mysterious character on an adventure."
        result = self.classifier.classify_context(context)
        self.assertEqual(result, ContentType.CREATIVE)

    def test_classify_dialogue_context(self):
        """Should detect dialogue markers."""
        context = '"Hello," said John. "How are you?" asked Mary: "I am fine."'
        result = self.classifier.classify_context(context)
        self.assertEqual(result, ContentType.DIALOGUE)

    def test_classify_list_context(self):
        """Should detect list content."""
        context = "Here are the items:\n- First item\n- Second item\n- Third item"
        result = self.classifier.classify_context(context)
        self.assertEqual(result, ContentType.LIST)

    def test_classify_prose_default(self):
        """Should default to prose for generic content."""
        context = "This is a simple sentence."
        result = self.classifier.classify_context(context)
        self.assertEqual(result, ContentType.PROSE)

    def test_get_dominant_type(self):
        """Should return most common recent type."""
        self.classifier.classify_context("def foo(): pass")
        self.classifier.classify_context("class Bar: pass")
        self.classifier.classify_context("import numpy")
        dominant = self.classifier.get_dominant_type(window=3)
        self.assertEqual(dominant, ContentType.CODE)

    def test_predict_next_type_code_marker(self):
        """Should predict CODE when seeing backticks."""
        result = self.classifier.predict_next_type(ContentType.PROSE, "```")
        self.assertEqual(result, ContentType.CODE)

    def test_history_tracking(self):
        """Should maintain classification history."""
        self.classifier.classify_context("def test(): pass")
        self.classifier.classify_context("Hello world")
        self.assertEqual(len(self.classifier.history), 2)


# =============================================================================
# MoE Router Tests
# =============================================================================
class TestMoERouter(unittest.TestCase):
    """Tests for MoERouter."""

    def setUp(self):
        self.models = {
            ContentType.CODE: create_mock_engine("code-model"),
            ContentType.PROSE: create_mock_engine("prose-model"),
        }
        self.router = MoERouter(self.models, verbose=False)

    def test_get_expert_for_content(self):
        """Should return correct expert for content type."""
        expert = self.router.get_expert_for_content(ContentType.CODE)
        self.assertEqual(expert.model_name, "code-model")

    def test_fallback_model(self):
        """Should use fallback for unknown content types."""
        expert = self.router.get_expert_for_content(ContentType.MATH)
        # Falls back to first model in dict
        self.assertIn(expert.model_name, ["code-model", "prose-model"])

    def test_routing_stats_tracking(self):
        """Should track routing statistics."""
        self.router.get_expert_for_content(ContentType.CODE)
        self.router.get_expert_for_content(ContentType.CODE)
        self.router.get_expert_for_content(ContentType.PROSE)

        self.assertEqual(self.router.routing_stats[ContentType.CODE], 2)
        self.assertEqual(self.router.routing_stats[ContentType.PROSE], 1)
        self.assertEqual(self.router.total_tokens, 3)

    def test_get_stats(self):
        """Should return proper statistics."""
        self.router.get_expert_for_content(ContentType.CODE)
        stats = self.router.get_stats()

        self.assertEqual(stats['total_tokens'], 1)
        self.assertIn('routing_distribution', stats)
        self.assertIn('available_experts', stats)

    def test_reset_stats(self):
        """Should reset all statistics."""
        self.router.get_expert_for_content(ContentType.CODE)
        self.router.reset_stats()

        self.assertEqual(self.router.total_tokens, 0)
        self.assertEqual(sum(self.router.routing_stats.values()), 0)


# =============================================================================
# Adaptive MoE Router Tests
# =============================================================================
class TestAdaptiveMoERouter(unittest.TestCase):
    """Tests for AdaptiveMoERouter."""

    def setUp(self):
        self.models = {
            ContentType.CODE: create_mock_engine("code-model"),
            ContentType.PROSE: create_mock_engine("prose-model"),
        }
        self.router = AdaptiveMoERouter(self.models, learning_rate=0.1, verbose=False)

    def test_initial_performance_scores(self):
        """Should initialize performance scores."""
        self.assertIn(ContentType.CODE, self.router.performance_scores)
        for model_name in ["code-model", "prose-model"]:
            self.assertEqual(
                self.router.performance_scores[ContentType.CODE].get(model_name, 0),
                1.0
            )

    def test_update_performance(self):
        """Should update performance with EMA."""
        initial = self.router.performance_scores[ContentType.CODE]["code-model"]
        self.router.update_performance(ContentType.CODE, "code-model", 0.5)
        updated = self.router.performance_scores[ContentType.CODE]["code-model"]

        # EMA: new = 0.9 * 1.0 + 0.1 * 0.5 = 0.95
        expected = (1 - 0.1) * initial + 0.1 * 0.5
        self.assertAlmostEqual(updated, expected, places=5)


# =============================================================================
# Speculative Decoding Tests
# =============================================================================
class TestSpeculativeDecoder(unittest.TestCase):
    """Tests for SpeculativeDecoder."""

    def setUp(self):
        self.draft = create_mock_engine("draft")
        self.target = create_mock_engine("target")
        self.decoder = SpeculativeDecoder(
            self.draft, self.target, k=4, verbose=False
        )

    def test_init(self):
        """Should initialize with correct parameters."""
        self.assertEqual(self.decoder.k, 4)
        self.assertEqual(self.decoder.draft_model, self.draft)
        self.assertEqual(self.decoder.target_model, self.target)

    def test_propose_tokens(self):
        """Should propose K tokens from draft model."""
        self.draft.get_eos_token_id.return_value = 999  # Won't hit EOS

        token_ids, token_texts, time_taken = self.decoder.propose_tokens(
            "Test context", num_tokens=3
        )

        self.assertEqual(len(token_ids), 3)
        self.assertEqual(len(token_texts), 3)
        self.assertGreater(time_taken, 0)

    def test_statistics_tracking(self):
        """Should track timing statistics."""
        self.draft.get_eos_token_id.return_value = 999
        self.decoder.propose_tokens("Test", num_tokens=2)

        self.assertGreater(self.decoder.total_time_draft, 0)

    def test_get_stats(self):
        """Should return comprehensive stats."""
        stats = self.decoder.get_stats()

        self.assertIn('total_proposed', stats)
        self.assertIn('total_accepted', stats)
        self.assertIn('k', stats)
        self.assertEqual(stats['k'], 4)

    def test_reset_stats(self):
        """Should reset all statistics."""
        self.decoder.total_proposed = 100
        self.decoder.total_accepted = 80
        self.decoder.reset_stats()

        self.assertEqual(self.decoder.total_proposed, 0)
        self.assertEqual(self.decoder.total_accepted, 0)


class TestSpeculativeResult(unittest.TestCase):
    """Tests for SpeculativeResult dataclass."""

    def test_create_result(self):
        """Should create result with all fields."""
        result = SpeculativeResult(
            accepted_tokens=[1, 2, 3],
            accepted_texts=["a", "b", "c"],
            num_proposed=5,
            num_accepted=3,
            acceptance_rate=0.6,
            speedup=1.5,
            time_taken=0.1
        )

        self.assertEqual(result.num_proposed, 5)
        self.assertEqual(result.acceptance_rate, 0.6)


# =============================================================================
# Contrastive Decoding Tests
# =============================================================================
class TestContrastiveConfig(unittest.TestCase):
    """Tests for ContrastiveConfig."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = ContrastiveConfig()
        self.assertEqual(config.alpha, 0.5)
        self.assertEqual(config.beta, 0.1)
        self.assertTrue(config.use_adaptive_alpha)


class TestContrastiveDecoder(unittest.TestCase):
    """Tests for ContrastiveDecoder."""

    def setUp(self):
        self.expert = create_mock_engine("expert")
        self.amateur = create_mock_engine("amateur")
        self.decoder = ContrastiveDecoder(
            self.expert, self.amateur, verbose=False
        )

    def test_softmax(self):
        """Should compute stable softmax."""
        logits = np.array([1.0, 2.0, 3.0])
        probs = self.decoder._softmax(logits)

        self.assertAlmostEqual(np.sum(probs), 1.0, places=5)
        self.assertTrue(np.all(probs >= 0))
        self.assertTrue(np.all(probs <= 1))

    def test_softmax_numerical_stability(self):
        """Should handle large logit values."""
        logits = np.array([1000.0, 1001.0, 1002.0])
        probs = self.decoder._softmax(logits)

        self.assertAlmostEqual(np.sum(probs), 1.0, places=5)
        self.assertFalse(np.any(np.isnan(probs)))

    def test_contrast_logits_shape(self):
        """Should produce correct output shape."""
        expert_logits = np.random.randn(100)
        amateur_logits = np.random.randn(100)

        result = self.decoder.contrast_logits(expert_logits, amateur_logits, alpha=0.5)
        self.assertEqual(result.shape, (100,))

    def test_contrast_logits_vocab_mismatch(self):
        """Should handle vocabulary size mismatch."""
        expert_logits = np.random.randn(100)
        amateur_logits = np.random.randn(80)

        result = self.decoder.contrast_logits(expert_logits, amateur_logits)
        self.assertEqual(result.shape, (80,))  # Takes minimum

    def test_calculate_adaptive_alpha(self):
        """Should compute adaptive alpha from KL divergence."""
        # Same distributions -> low alpha
        same_logits = np.array([1.0, 2.0, 3.0])
        alpha_same = self.decoder.calculate_adaptive_alpha(same_logits, same_logits)
        self.assertLessEqual(alpha_same, 0.2)

        # Different distributions -> higher alpha
        expert = np.array([5.0, 1.0, 0.0])
        amateur = np.array([0.0, 1.0, 5.0])
        alpha_diff = self.decoder.calculate_adaptive_alpha(expert, amateur)
        self.assertGreater(alpha_diff, alpha_same)

    def test_get_stats(self):
        """Should return comprehensive stats."""
        stats = self.decoder.get_stats()

        self.assertIn('total_tokens', stats)
        self.assertIn('config', stats)
        self.assertEqual(stats['config']['alpha'], 0.5)

    def test_reset_stats(self):
        """Should reset all statistics."""
        self.decoder.total_tokens = 100
        self.decoder.avg_expert_confidence = 0.9
        self.decoder.reset_stats()

        self.assertEqual(self.decoder.total_tokens, 0)
        self.assertEqual(self.decoder.avg_expert_confidence, 0.0)


# =============================================================================
# Feedback Loop Tests
# =============================================================================
class TestFeedbackType(unittest.TestCase):
    """Tests for FeedbackType enum."""

    def test_all_types_defined(self):
        """Should have all feedback types."""
        types = [FeedbackType.GRAMMAR, FeedbackType.COHERENCE,
                 FeedbackType.FACTUALITY, FeedbackType.STYLE,
                 FeedbackType.COMPLETENESS, FeedbackType.RELEVANCE]
        self.assertEqual(len(types), 6)


class TestFeedback(unittest.TestCase):
    """Tests for Feedback dataclass."""

    def test_create_feedback(self):
        """Should create feedback with all fields."""
        fb = Feedback(
            feedback_type=FeedbackType.GRAMMAR,
            score=0.8,
            comments="Good grammar",
            suggestions=["Check punctuation"],
            needs_revision=False
        )
        self.assertEqual(fb.score, 0.8)
        self.assertFalse(fb.needs_revision)


class TestFeedbackLoop(unittest.TestCase):
    """Tests for FeedbackLoop."""

    def setUp(self):
        self.generator = create_mock_engine("generator")
        self.critic = create_mock_engine("critic")
        self.loop = FeedbackLoop(
            self.generator, self.critic,
            max_iterations=3,
            min_score_threshold=0.8,
            verbose=False
        )

    def test_estimate_quality_score_short_text(self):
        """Should penalize very short text."""
        score = self.loop._estimate_quality_score("Hi", FeedbackType.GRAMMAR)
        self.assertLess(score, 0.5)

    def test_estimate_quality_score_grammar(self):
        """Should evaluate grammar heuristics."""
        good_text = "This is a proper sentence. It continues well."
        score = self.loop._estimate_quality_score(good_text, FeedbackType.GRAMMAR)
        self.assertGreater(score, 0.3)

    def test_estimate_quality_score_coherence(self):
        """Should detect coherence markers."""
        coherent = "First, we explain. However, there is more. Therefore, we conclude."
        score = self.loop._estimate_quality_score(coherent, FeedbackType.COHERENCE)
        self.assertGreater(score, 0.5)

    def test_generate_suggestions_low_score(self):
        """Should generate suggestions for low scores."""
        suggestions = self.loop._generate_suggestions("text", FeedbackType.GRAMMAR, 0.3)
        self.assertGreater(len(suggestions), 0)

    def test_generate_suggestions_high_score(self):
        """Should not generate suggestions for high scores."""
        suggestions = self.loop._generate_suggestions("text", FeedbackType.GRAMMAR, 0.9)
        self.assertEqual(len(suggestions), 0)

    def test_get_stats(self):
        """Should return comprehensive stats."""
        stats = self.loop.get_stats()

        self.assertIn('total_iterations', stats)
        self.assertIn('max_iterations', stats)
        self.assertEqual(stats['max_iterations'], 3)


class TestFeedbackResult(unittest.TestCase):
    """Tests for FeedbackResult dataclass."""

    def test_create_result(self):
        """Should create result with all fields."""
        result = FeedbackResult(
            original_text="Hello",
            revised_text="Hello, world!",
            feedbacks=[],
            num_iterations=2,
            improvement_score=0.3,
            converged=True
        )
        self.assertTrue(result.converged)
        self.assertEqual(result.improvement_score, 0.3)


# =============================================================================
# Hierarchical Control Tests
# =============================================================================
class TestPlanStep(unittest.TestCase):
    """Tests for PlanStep enum."""

    def test_all_steps_defined(self):
        """Should have all plan step types."""
        steps = [PlanStep.INTRODUCE, PlanStep.EXPLAIN, PlanStep.PROVIDE_EVIDENCE,
                 PlanStep.ANALYZE, PlanStep.SYNTHESIZE, PlanStep.CONCLUDE,
                 PlanStep.CODE_EXAMPLE, PlanStep.ENUMERATE]
        self.assertEqual(len(steps), 8)


class TestExecutionPlan(unittest.TestCase):
    """Tests for ExecutionPlan dataclass."""

    def test_create_plan(self):
        """Should create plan with all fields."""
        steps = [(PlanStep.INTRODUCE, "Intro"), (PlanStep.CONCLUDE, "End")]
        plan = ExecutionPlan(
            steps=steps,
            objective="Test objective",
            constraints={'max_steps': 5}
        )
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.objective, "Test objective")


class TestHierarchicalController(unittest.TestCase):
    """Tests for HierarchicalController."""

    def setUp(self):
        self.meta = create_mock_engine("meta")
        self.specialists = {
            PlanStep.CODE_EXAMPLE: create_mock_engine("code-specialist"),
            PlanStep.EXPLAIN: create_mock_engine("explain-specialist"),
        }
        self.controller = HierarchicalController(
            self.meta, self.specialists, verbose=False
        )

    def test_generate_plan_steps_code(self):
        """Should generate code-focused plan for code objectives."""
        steps = self.controller._generate_plan_steps(
            "Write a function to calculate factorial", max_steps=5
        )
        step_types = [s[0] for s in steps]
        self.assertIn(PlanStep.CODE_EXAMPLE, step_types)

    def test_generate_plan_steps_explanation(self):
        """Should generate explanation plan for explain objectives."""
        steps = self.controller._generate_plan_steps(
            "What is machine learning?", max_steps=5
        )
        step_types = [s[0] for s in steps]
        self.assertIn(PlanStep.EXPLAIN, step_types)

    def test_generate_plan_steps_generic(self):
        """Should generate generic plan for other objectives."""
        steps = self.controller._generate_plan_steps(
            "Hello world", max_steps=3
        )
        self.assertLessEqual(len(steps), 3)

    def test_create_plan(self):
        """Should create complete execution plan."""
        plan = self.controller.create_plan("Explain neural networks", max_steps=5)

        self.assertEqual(plan.objective, "Explain neural networks")
        self.assertLessEqual(len(plan.steps), 5)
        self.assertEqual(plan.constraints['max_steps'], 5)


class TestExecutionResult(unittest.TestCase):
    """Tests for ExecutionResult dataclass."""

    def test_create_result(self):
        """Should create result with all fields."""
        plan = ExecutionPlan(
            steps=[(PlanStep.INTRODUCE, "Intro")],
            objective="Test",
            constraints={}
        )
        result = ExecutionResult(
            plan=plan,
            generated_text="Generated content",
            steps_completed=1,
            success=True,
            metadata={'completion_rate': 1.0}
        )
        self.assertTrue(result.success)
        self.assertEqual(result.steps_completed, 1)


# =============================================================================
# Adversarial Debate Tests
# =============================================================================
class TestClaim(unittest.TestCase):
    """Tests for Claim dataclass."""

    def test_create_claim(self):
        """Should create claim with all fields."""
        claim = Claim(
            text="AI is beneficial",
            confidence=0.8,
            supporting_evidence=["Evidence 1", "Evidence 2"]
        )
        self.assertEqual(claim.text, "AI is beneficial")
        self.assertEqual(len(claim.supporting_evidence), 2)


class TestChallenge(unittest.TestCase):
    """Tests for Challenge dataclass."""

    def test_create_challenge(self):
        """Should create challenge with all fields."""
        claim = Claim("Test claim", 0.8, [])
        challenge = Challenge(
            claim=claim,
            challenge_text="But what about...",
            counter_evidence=["Counter 1"],
            strength=0.7
        )
        self.assertEqual(challenge.strength, 0.7)


class TestDebateResult(unittest.TestCase):
    """Tests for DebateResult dataclass."""

    def test_create_result(self):
        """Should create debate result with all fields."""
        claim = Claim("Test", 0.8, [])
        result = DebateResult(
            original_claim=claim,
            challenges=[],
            final_consensus="We conclude...",
            confidence_score=0.75,
            rounds=3
        )
        self.assertEqual(result.rounds, 3)
        self.assertEqual(result.confidence_score, 0.75)


class TestAdversarialDebate(unittest.TestCase):
    """Tests for AdversarialDebate."""

    def setUp(self):
        self.red = create_mock_engine("red")
        self.blue = create_mock_engine("blue")
        self.debate = AdversarialDebate(
            self.red, self.blue,
            max_rounds=3,
            verbose=False
        )

    def test_init(self):
        """Should initialize with correct parameters."""
        self.assertEqual(self.debate.max_rounds, 3)
        self.assertEqual(self.debate.red_team, self.red)
        self.assertEqual(self.debate.blue_team, self.blue)

    def test_synthesize_consensus_confidence(self):
        """Should calculate confidence based on challenge strength."""
        claim = Claim("Test", 0.8, [])
        challenges = [
            Challenge(claim, "Challenge 1", [], 0.5),
            Challenge(claim, "Challenge 2", [], 0.7)
        ]

        # Mock the synthesis
        self.red.get_eos_token_id.return_value = 5  # Will hit EOS quickly

        consensus, confidence = self.debate.synthesize_consensus(
            claim, challenges, temperature=0.5
        )

        # Confidence should be reduced based on challenge strength
        # avg strength = 0.6, so confidence ~ 0.8 * (1 - 0.3 * 0.6) = 0.656
        self.assertLess(confidence, claim.confidence)


# =============================================================================
# Integration Tests
# =============================================================================
class TestModuleInteroperability(unittest.TestCase):
    """Test that modules can work together."""

    def test_moe_with_content_classifier(self):
        """MoE router should work with content classifier."""
        classifier = ContentClassifier()
        models = {
            ContentType.CODE: create_mock_engine("code"),
        }
        router = MoERouter(models, classifier=classifier)

        self.assertIs(router.classifier, classifier)

    def test_adaptive_router_extends_base(self):
        """Adaptive router should extend base router functionality."""
        models = {ContentType.CODE: create_mock_engine("code")}
        router = AdaptiveMoERouter(models)

        # Should have both base and adaptive methods
        self.assertTrue(hasattr(router, 'get_expert_for_content'))
        self.assertTrue(hasattr(router, 'update_performance'))


if __name__ == "__main__":
    unittest.main()
