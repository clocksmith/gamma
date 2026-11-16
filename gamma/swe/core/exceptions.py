"""
Agent exceptions hierarchy.

NonTerminatingException: Can be handled, agent continues
TerminatingException: Agent must stop
"""


class AgentException(Exception):
    """Base exception for all agent errors."""
    pass


# --- Non-terminating (recoverable) ---

class NonTerminatingException(AgentException):
    """Raised for conditions that can be handled by the agent."""
    pass


class FormatError(NonTerminatingException):
    """Raised when the model's output is not in expected format."""
    pass


class ExecutionTimeoutError(NonTerminatingException):
    """Raised when tool execution timed out."""
    def __init__(self, message: str, partial_output: str = ""):
        super().__init__(message)
        self.partial_output = partial_output


class ThresholdNotMet(NonTerminatingException):
    """Raised when ring score doesn't meet conductor's threshold."""
    def __init__(self, message: str, best_score: float, threshold: float):
        super().__init__(message)
        self.best_score = best_score
        self.threshold = threshold


class ToolNotFound(NonTerminatingException):
    """Raised when requested tool doesn't exist."""
    pass


class ToolExecutionError(NonTerminatingException):
    """Raised when tool execution fails."""
    def __init__(self, message: str, tool_name: str, error: str):
        super().__init__(message)
        self.tool_name = tool_name
        self.error = error


# --- Terminating (agent must stop) ---

class TerminatingException(AgentException):
    """Raised for conditions that terminate the agent."""
    pass


class Submitted(TerminatingException):
    """Raised when agent declares task is complete."""
    def __init__(self, result: str):
        super().__init__(f"Task completed: {result[:100]}...")
        self.result = result


class LimitsExceeded(TerminatingException):
    """Raised when agent reaches cost or step limit."""
    def __init__(self, limit_type: str, current: float, limit: float):
        super().__init__(f"{limit_type} limit exceeded: {current:.2f} >= {limit:.2f}")
        self.limit_type = limit_type
        self.current = current
        self.limit = limit


class CostLimitExceeded(LimitsExceeded):
    """Raised when cost limit is exceeded."""
    def __init__(self, current: float, limit: float):
        super().__init__("Cost", current, limit)


class StepLimitExceeded(LimitsExceeded):
    """Raised when step limit is exceeded."""
    def __init__(self, current: int, limit: int):
        super().__init__("Step", float(current), float(limit))


class MaxRoundsExceeded(TerminatingException):
    """Raised when ring exceeds max rounds without meeting threshold."""
    pass


class FatalError(TerminatingException):
    """Raised for unrecoverable errors."""
    pass
