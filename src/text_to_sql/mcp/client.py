"""MCP client implementation following modelcontextprotocol.io specifications."""

import logging
import time
from dataclasses import asdict
from typing import Dict, List, Optional

import httpx

from text_to_sql.core.config import settings
from text_to_sql.mcp.models import (
	ChatCompletionChoice,
	ChatCompletionMessage,
	CompletionRequest,
	CompletionResponse,
	Message,
	MessageRole,
)

logger = logging.getLogger(__name__)


class MCPClient:
	"""Model Context Protocol client."""

	def __init__(
		self,
		server_url: Optional[str] = None,
		api_key: Optional[str] = None,
		default_model: Optional[str] = None,
		timeout: Optional[int] = None,
	):
		"""Initialize the MCP client."""
		self.server_url = server_url or settings.mcp_config.server_url
		self.api_key = api_key or settings.mcp_config.api_key
		self.default_model = default_model or settings.mcp_config.default_model
		self.timeout = timeout or settings.mcp_config.timeout

		if not self.server_url:
			raise ValueError('MCP server URL is required')

		# Ensure server URL doesn't end with slash
		if self.server_url.endswith('/'):
			self.server_url = self.server_url[:-1]

		logger.info(f'Initialized MCP client with server URL: {self.server_url}')

	async def _make_request(self, endpoint: str, data: Dict) -> Dict:
		"""Make a request to the MCP server."""
		url = f'{self.server_url}/{endpoint}'
		headers = {'Content-Type': 'application/json'}

		if self.api_key:
			headers['Authorization'] = f'Bearer {self.api_key}'

		async with httpx.AsyncClient(timeout=self.timeout) as client:
			logger.debug(f'Making request to {url}')
			response = await client.post(url, json=data, headers=headers)

			if response.status_code != 200:
				logger.error(f'MCP request failed: {response.status_code} {response.text}')
				response.raise_for_status()

			return response.json()

	async def complete(
		self,
		messages: List[Message],
		model: Optional[str] = None,
		temperature: float = 0.0,
		max_tokens: Optional[int] = None,
		stream: bool = False,
		**kwargs,
	) -> CompletionResponse:
		"""Generate a completion using the MCP API."""
		request = CompletionRequest(
			messages=messages,
			model=model or self.default_model,
			temperature=temperature,
			max_tokens=max_tokens,
			stream=stream,
			**kwargs,
		)

		start_time = time.time()
		response_data = await self._make_request('chat/completions', asdict(request))
		elapsed = time.time() - start_time

		logger.debug(f'Completion request completed in {elapsed:.2f}s')

		# Create message object from response
		choices = []
		for choice_data in response_data.get('choices', []):
			message_data = choice_data.get('message', {})
			message = ChatCompletionMessage(
				role=message_data.get('role', 'assistant'),
				content=message_data.get('content', ''),
			)
			choice = ChatCompletionChoice(
				index=choice_data.get('index', 0),
				message=message,
				finish_reason=choice_data.get('finish_reason', ''),
			)
			choices.append(choice)

		return CompletionResponse(
			id=response_data.get('id', ''),
			choices=[asdict(choice) for choice in choices],
			model=response_data.get('model', ''),
			created=response_data.get('created', int(time.time())),
			usage=response_data.get('usage', {}),
		)

	async def generate_sql(
		self,
		natural_language_query: str,
		schema_context: str,
		**kwargs,
	) -> str:
		"""Generate SQL from natural language using the model."""
		from text_to_sql.mcp.prompts import get_sql_generation_prompt

		system_prompt, user_prompt = get_sql_generation_prompt(
			natural_language_query=natural_language_query, schema_context=schema_context
		)

		messages = [
			Message(role=MessageRole.SYSTEM, content=system_prompt),
			Message(role=MessageRole.USER, content=user_prompt),
		]

		response = await self.complete(
			messages=messages,
			temperature=0.0,  # Use exact value for SQL generation
			**kwargs,
		)

		if not response.choices:
			raise ValueError('No completion choices returned from MCP API')

		sql = response.choices[0]['message']['content'].strip()
		return self._extract_sql_from_response(sql)

	def _extract_sql_from_response(self, response: str) -> str:
		"""Extract SQL query from model response."""
		# Look for SQL query in code blocks
		if '```sql' in response:
			# Extract SQL from markdown code block
			start_idx = response.find('```sql') + 6
			end_idx = response.find('```', start_idx)
			if end_idx > start_idx:
				return response[start_idx:end_idx].strip()

		if '```' in response:
			# Extract from generic code block
			start_idx = response.find('```') + 3
			# Skip language identifier if present
			if '\n' in response[start_idx:]:
				newline_idx = response.find('\n', start_idx)
				start_idx = newline_idx + 1
			end_idx = response.find('```', start_idx)
			if end_idx > start_idx:
				return response[start_idx:end_idx].strip()

		# Return the whole response if no code blocks found
		# Postprocessing will handle this
		return response
