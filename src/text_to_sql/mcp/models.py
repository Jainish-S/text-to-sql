"""Model Context Protocol data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(str, Enum):
	"""Message role in a conversation."""

	SYSTEM = 'system'
	USER = 'user'
	ASSISTANT = 'assistant'


@dataclass
class Message:
	"""Message in a conversation."""

	role: MessageRole
	content: str


@dataclass
class CompletionRequest:
	"""Request for model completion."""

	messages: List[Message]
	model: str
	temperature: float = 0.0
	max_tokens: Optional[int] = None
	stream: bool = False
	top_p: Optional[float] = None
	frequency_penalty: Optional[float] = None
	presence_penalty: Optional[float] = None
	stop: Optional[List[str]] = None
	extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionResponse:
	"""Response from model completion."""

	id: str
	choices: List[Dict[str, Any]]
	model: str
	created: int
	usage: Dict[str, int]


@dataclass
class ChatCompletionMessage:
	"""Message in chat completion response."""

	role: str
	content: str


@dataclass
class ChatCompletionChoice:
	"""Choice in chat completion response."""

	index: int
	message: ChatCompletionMessage
	finish_reason: str
