"""
Base agent class with full infrastructure.

Provides:
- Message history tracking
- Cost/step limits
- Template rendering
- Trajectory saving
- Proper exception handling
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from jinja2 import Template, StrictUndefined

from .exceptions import (
    CostLimitExceeded,
    StepLimitExceeded,
    NonTerminatingException,
    TerminatingException,
    Submitted,
)
from .history import History, Message, MessageRole
from .trajectory import Trajectory, save_trajectory


@dataclass
class AgentConfig:
    """Agent configuration."""
    # Limits
    step_limit: int = 0  # 0 = unlimited
    cost_limit: float = 10.0  # 0 = unlimited

    # Templates (Jinja2)
    system_template: str = "You are an expert software engineer."
    task_template: str = "Task: {{ task }}"
    observation_template: str = "Observation:\n{{ output }}"
    error_template: str = "Error: {{ error }}"
    timeout_template: str = "Execution timed out after {{ timeout }}s. Partial output:\n{{ output }}"

    # Ring settings
    default_threshold: float = 0.8
    max_rounds: int = 10

    # Output
    output_dir: Optional[str] = None
    save_trajectory: bool = True


class BaseAgent:
    """
    Base agent with full infrastructure.

    Subclass and override:
    - step() for custom agent logic
    - parse_action() for custom action parsing
    - execute_action() for custom execution
    """

    def __init__(
        self,
        model,
        config: Optional[AgentConfig] = None,
        **kwargs,
    ):
        self.model = model
        self.config = config or AgentConfig(**kwargs)
        self.history = History()
        self.trajectory: Optional[Trajectory] = None
        self.extra_template_vars: Dict[str, Any] = {}

    def render_template(self, template: str, **kwargs) -> str:
        """Render a Jinja2 template."""
        all_vars = {
            **self.config.__dict__,
            **self.extra_template_vars,
            **kwargs,
        }
        try:
            return Template(template, undefined=StrictUndefined).render(**all_vars)
        except Exception:
            # Fallback to simple string formatting
            return template.format(**all_vars) if "{" in template else template

    def check_limits(self) -> None:
        """Check if limits are exceeded. Raises if so."""
        if self.config.step_limit > 0 and self.history.n_steps >= self.config.step_limit:
            raise StepLimitExceeded(self.history.n_steps, self.config.step_limit)

        if self.config.cost_limit > 0 and self.history.total_cost >= self.config.cost_limit:
            raise CostLimitExceeded(self.history.total_cost, self.config.cost_limit)

    def run(self, task: str, **kwargs) -> tuple[str, str]:
        """
        Run agent until completion.

        Returns:
            (exit_status, result) tuple
        """
        self.extra_template_vars = {"task": task, **kwargs}
        self.history = History()
        self.trajectory = Trajectory(
            task=task,
            model_name=getattr(self.model, "model_name", "unknown"),
            config=self.config.__dict__,
        )

        # Add system message
        system_msg = self.render_template(self.config.system_template)
        self.history.add_system(system_msg)

        # Add task message
        task_msg = self.render_template(self.config.task_template)
        self.history.add_user(task_msg)

        exit_status = "Unknown"
        result = ""

        try:
            while True:
                try:
                    self.check_limits()
                    self.step()
                except NonTerminatingException as e:
                    # Recoverable - add to history and continue
                    error_msg = self.render_template(
                        self.config.error_template,
                        error=str(e),
                    )
                    self.history.add_user(error_msg)
                except TerminatingException as e:
                    exit_status = type(e).__name__
                    result = str(e)
                    if isinstance(e, Submitted):
                        result = e.result
                    break

        except Exception as e:
            exit_status = "Error"
            result = str(e)

        finally:
            # Save trajectory
            if self.trajectory:
                self.trajectory.history = self.history
                self.trajectory.finish(exit_status, result)

                if self.config.save_trajectory and self.config.output_dir:
                    output_path = Path(self.config.output_dir) / f"traj_{int(time.time())}.json"
                    save_trajectory(self.trajectory, output_path)

        return exit_status, result

    def step(self) -> None:
        """
        Execute one agent step.

        Override in subclasses for custom logic.
        Default: query model, parse action, execute, observe.
        """
        self.history.increment_step()

        # Query model
        response = self.query()

        # Parse and execute action
        action = self.parse_action(response)
        output = self.execute_action(action)

        # Add observation
        observation = self.render_template(
            self.config.observation_template,
            output=output,
        )
        self.history.add_observation(observation)

        # Check for submission
        self.check_submission(output)

    def query(self) -> str:
        """Query the model."""
        messages = self.history.to_chat_format()

        # Call model (assumes async, but we'll handle sync too)
        if hasattr(self.model, "generate"):
            import asyncio
            if asyncio.iscoroutinefunction(self.model.generate):
                response = asyncio.get_event_loop().run_until_complete(
                    self.model.generate(messages[-1]["content"])
                )
            else:
                response = self.model.generate(messages[-1]["content"])
        elif hasattr(self.model, "chat"):
            import asyncio
            if asyncio.iscoroutinefunction(self.model.chat):
                response = asyncio.get_event_loop().run_until_complete(
                    self.model.chat(messages[-1]["content"])
                )
            else:
                response = self.model.chat(messages[-1]["content"])
        else:
            response = str(self.model(messages))

        self.history.add_assistant(response)
        return response

    def parse_action(self, response: str) -> Dict[str, Any]:
        """
        Parse action from model response.

        Override for custom parsing.
        Default: look for JSON tool call.
        """
        import json
        import re

        # Try JSON in code block
        json_match = re.search(r"```(?:json)?\s*\n?({.*?})\s*\n?```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try raw JSON
        try:
            if "{" in response:
                json_str = response[response.index("{"):response.rindex("}")+1]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: treat as raw action
        return {"action": response.strip()}

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action.

        Override for custom execution.
        """
        # Default: return action as-is (subclasses implement real execution)
        return {"output": str(action), "action": action}

    def check_submission(self, output: Dict[str, Any]) -> None:
        """Check if agent is submitting final result."""
        output_str = str(output.get("output", ""))
        lines = output_str.strip().splitlines()

        if lines:
            first_line = lines[0].strip()
            if first_line in ["SUBMIT", "DONE", "COMPLETE", "FINISHED"]:
                result = "\n".join(lines[1:]) if len(lines) > 1 else ""
                raise Submitted(result)
