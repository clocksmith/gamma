"""
Message history tracking.

Tracks all messages, tool calls, and observations during agent execution.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    OBSERVATION = "observation"


@dataclass
class Message:
    """Single message in conversation history."""
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # For tool calls
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None

    # For scoring
    score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
        }
        if self.metadata:
            d["metadata"] = self.metadata
        if self.tool_name:
            d["tool_name"] = self.tool_name
        if self.tool_args:
            d["tool_args"] = self.tool_args
        if self.tool_result is not None:
            d["tool_result"] = self.tool_result
        if self.score is not None:
            d["score"] = self.score
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            role=MessageRole(d["role"]),
            content=d["content"],
            timestamp=d.get("timestamp", time.time()),
            metadata=d.get("metadata", {}),
            tool_name=d.get("tool_name"),
            tool_args=d.get("tool_args"),
            tool_result=d.get("tool_result"),
            score=d.get("score"),
        )


class History:
    """
    Conversation history with message tracking.

    Supports:
    - Adding messages with roles
    - Filtering by role
    - Cost/token tracking
    - Serialization
    """

    def __init__(self):
        self.messages: List[Message] = []
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.n_steps: int = 0
        self.start_time: float = time.time()

    def add(
        self,
        role: MessageRole,
        content: str,
        **kwargs,
    ) -> Message:
        """Add a message to history."""
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        return msg

    def add_system(self, content: str, **kwargs) -> Message:
        return self.add(MessageRole.SYSTEM, content, **kwargs)

    def add_user(self, content: str, **kwargs) -> Message:
        return self.add(MessageRole.USER, content, **kwargs)

    def add_assistant(self, content: str, **kwargs) -> Message:
        return self.add(MessageRole.ASSISTANT, content, **kwargs)

    def add_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Any,
        score: Optional[float] = None,
    ) -> Message:
        """Add a tool call with its result."""
        return self.add(
            MessageRole.TOOL,
            f"Tool: {tool_name}",
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=result,
            score=score,
        )

    def add_observation(self, content: str, **kwargs) -> Message:
        return self.add(MessageRole.OBSERVATION, content, **kwargs)

    def add_cost(self, tokens: int, cost: float) -> None:
        """Track token usage and cost."""
        self.total_tokens += tokens
        self.total_cost += cost

    def increment_step(self) -> int:
        """Increment step counter."""
        self.n_steps += 1
        return self.n_steps

    def get_messages(self, role: Optional[MessageRole] = None) -> List[Message]:
        """Get messages, optionally filtered by role."""
        if role is None:
            return self.messages
        return [m for m in self.messages if m.role == role]

    def get_last(self, role: Optional[MessageRole] = None) -> Optional[Message]:
        """Get last message, optionally filtered by role."""
        msgs = self.get_messages(role)
        return msgs[-1] if msgs else None

    def to_chat_format(self) -> List[Dict[str, str]]:
        """Convert to chat format for LLM APIs."""
        chat = []
        for msg in self.messages:
            if msg.role in (MessageRole.SYSTEM, MessageRole.USER, MessageRole.ASSISTANT):
                chat.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })
        return chat

    def to_dict(self) -> Dict[str, Any]:
        """Serialize history."""
        return {
            "messages": [m.to_dict() for m in self.messages],
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "n_steps": self.n_steps,
            "start_time": self.start_time,
            "duration": time.time() - self.start_time,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "History":
        """Deserialize history."""
        h = cls()
        h.messages = [Message.from_dict(m) for m in d.get("messages", [])]
        h.total_tokens = d.get("total_tokens", 0)
        h.total_cost = d.get("total_cost", 0.0)
        h.n_steps = d.get("n_steps", 0)
        h.start_time = d.get("start_time", time.time())
        return h

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)
