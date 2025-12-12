"""
Hierarchical Control for Mind Meld.

A "conductor" or meta-model creates high-level plans and coordinates
specialist models to execute each part of the plan.
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.engine_interface import LLMEngine
from src.mind_meld.utils import VerboseLoggerMixin


class PlanStep(Enum):
    """Types of plan steps."""
    INTRODUCE = "introduce"
    EXPLAIN = "explain"
    PROVIDE_EVIDENCE = "provide_evidence"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    CONCLUDE = "conclude"
    CODE_EXAMPLE = "code_example"
    ENUMERATE = "enumerate"


@dataclass
class ExecutionPlan:
    """High-level execution plan."""
    steps: List[Tuple[PlanStep, str]]  # (step_type, description)
    objective: str
    constraints: Dict[str, Any]


@dataclass
class ExecutionResult:
    """Result of executing a plan."""
    plan: ExecutionPlan
    generated_text: str
    steps_completed: int
    success: bool
    metadata: Dict[str, Any]


class HierarchicalController(VerboseLoggerMixin):
    """
    Hierarchical control system for Mind Meld.

    Meta-model creates plans, specialist models execute them.
    """

    def __init__(
        self,
        meta_model: LLMEngine,
        specialist_models: Dict[PlanStep, LLMEngine],
        verbose: bool = False
    ):
        """
        Initialize hierarchical controller.

        Args:
            meta_model: Model for planning and coordination
            specialist_models: Dict mapping plan steps to specialist models
            verbose: Enable verbose logging
        """
        self.meta_model = meta_model
        self.specialists = specialist_models
        self.verbose = verbose

    def create_plan(self, objective: str, max_steps: int = 5) -> ExecutionPlan:
        """
        Create execution plan for objective.

        Args:
            objective: High-level objective
            max_steps: Maximum plan steps

        Returns:
            ExecutionPlan
        """
        self._log(f"Creating plan for: {objective}")

        # Build planning prompt
        planning_prompt = f"""Create a structured plan to accomplish the following objective:

Objective: {objective}

Provide a step-by-step plan with {max_steps} steps. For each step, specify:
1. Step type (introduce, explain, provide_evidence, analyze, synthesize, conclude, code_example, enumerate)
2. Brief description

Plan:"""

        # Generate plan (simplified - in practice would parse structured output)
        steps = self._generate_plan_steps(planning_prompt, max_steps)

        return ExecutionPlan(
            steps=steps,
            objective=objective,
            constraints={'max_steps': max_steps}
        )

    def _generate_plan_steps(
        self,
        prompt: str,
        max_steps: int
    ) -> List[Tuple[PlanStep, str]]:
        """Generate plan steps using meta-model."""
        # Simplified: return a reasonable default plan
        # In practice, would parse meta-model output

        # Detect objective type for smart planning
        prompt_lower = prompt.lower()

        if 'code' in prompt_lower or 'function' in prompt_lower:
            return [
                (PlanStep.INTRODUCE, "Introduce the coding problem"),
                (PlanStep.EXPLAIN, "Explain the approach"),
                (PlanStep.CODE_EXAMPLE, "Provide code implementation"),
                (PlanStep.ANALYZE, "Analyze the solution"),
                (PlanStep.CONCLUDE, "Summarize key points")
            ]
        elif 'explain' in prompt_lower or 'what' in prompt_lower:
            return [
                (PlanStep.INTRODUCE, "Introduce the topic"),
                (PlanStep.EXPLAIN, "Provide detailed explanation"),
                (PlanStep.PROVIDE_EVIDENCE, "Give examples"),
                (PlanStep.ANALYZE, "Analyze implications"),
                (PlanStep.CONCLUDE, "Conclude with summary")
            ]
        else:
            # Generic plan
            return [
                (PlanStep.INTRODUCE, "Introduction"),
                (PlanStep.EXPLAIN, "Main content"),
                (PlanStep.CONCLUDE, "Conclusion")
            ][:max_steps]

    def execute_step(
        self,
        step: PlanStep,
        description: str,
        context: str,
        temperature: float = 0.7
    ) -> str:
        """
        Execute a single plan step.

        Args:
            step: Step type
            description: Step description
            context: Current context
            temperature: Sampling temperature

        Returns:
            Generated text for this step
        """
        self._log(f"Executing step: {step.value} - {description}")

        # Get specialist for this step
        specialist = self.specialists.get(step)
        if specialist is None:
            # Use meta-model as fallback
            specialist = self.meta_model

        # Build execution prompt
        execution_prompt = f"""{context}

[Task: {description}]

"""

        # Generate for this step (limited tokens)
        generated = ""
        max_tokens = 150  # Per step limit

        for _ in range(max_tokens):
            input_ids, attention_mask = specialist.encode(
                execution_prompt + generated,
                add_special_tokens=True
            )
            result = specialist.predict_next(
                input_ids,
                attention_mask,
                temperature=temperature,
                top_k=50,
                top_p=0.95
            )

            token_id = result['next_token_id']
            token_text = specialist.get_token_text(token_id)
            generated += token_text

            # Stop at natural boundaries
            if token_id == specialist.get_eos_token_id():
                break
            if '\n\n' in generated:
                # End of paragraph
                break

        return generated.strip()

    def execute_plan(
        self,
        plan: ExecutionPlan,
        temperature: float = 0.7
    ) -> ExecutionResult:
        """
        Execute complete plan.

        Args:
            plan: Execution plan
            temperature: Sampling temperature

        Returns:
            ExecutionResult with generated text
        """
        self._log(f"Executing plan with {len(plan.steps)} steps")

        generated_text = f"# {plan.objective}\n\n"
        context = generated_text
        steps_completed = 0

        for step_type, description in plan.steps:
            try:
                step_output = self.execute_step(
                    step_type,
                    description,
                    context,
                    temperature
                )

                generated_text += step_output + "\n\n"
                context = generated_text
                steps_completed += 1

            except Exception as e:
                self._log(f"Error executing step: {e}")
                break

        return ExecutionResult(
            plan=plan,
            generated_text=generated_text,
            steps_completed=steps_completed,
            success=steps_completed == len(plan.steps),
            metadata={
                'total_steps': len(plan.steps),
                'completion_rate': steps_completed / len(plan.steps)
            }
        )

    def generate_with_planning(
        self,
        objective: str,
        max_steps: int = 5,
        temperature: float = 0.7
    ) -> Tuple[str, ExecutionPlan]:
        """
        Generate text with hierarchical planning.

        Args:
            objective: High-level objective
            max_steps: Maximum plan steps
            temperature: Sampling temperature

        Returns:
            (generated_text, execution_plan)
        """
        # Create plan
        plan = self.create_plan(objective, max_steps)

        # Execute plan
        result = self.execute_plan(plan, temperature)

        return result.generated_text, plan
