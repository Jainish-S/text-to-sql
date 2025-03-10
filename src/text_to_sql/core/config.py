"""Application configuration settings."""

from dataclasses import dataclass
from typing import List, Literal, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class MCPConfig:
	"""Model Context Protocol configuration."""

	server_url: str = 'http://localhost:8000/v1'
	api_key: Optional[str] = None
	default_model: str = 'openai/gpt-4'
	timeout: int = 60


class Settings(BaseSettings):
	"""Application settings."""

	# API settings
	API_HOST: str = '0.0.0.0'
	API_PORT: int = 8000
	CORS_ORIGINS: List[str] = ['*']

	# Database settings
	DB_USER: str = Field(default='postgres')
	DB_PASSWORD: str = Field(default='postgres', repr=False)
	DB_HOST: str = Field(default='localhost')
	DB_PORT: int = Field(default=5432)
	DB_NAME: str = Field(default='postgres')
	DB_MIN_CONNECTIONS: int = 5
	DB_MAX_CONNECTIONS: int = 20

	# Cache settings
	SCHEMA_CACHE_TTL: int = 3600  # seconds

	# MCP settings
	MCP_SERVER_URL: str = Field(default='http://localhost:8000/v1')
	MCP_API_KEY: Optional[str] = Field(default=None, repr=False)
	MCP_DEFAULT_MODEL: str = 'openai/gpt-4'
	MCP_TIMEOUT: int = 60

	# LLM settings
	LLM_PROVIDER: Literal['openai', 'anthropic'] = 'openai'
	OPENAI_API_KEY: Optional[str] = Field(default=None, repr=False)
	ANTHROPIC_API_KEY: Optional[str] = Field(default=None, repr=False)

	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

	@computed_field
	@property
	def DATABASE_URL(self) -> str:
		"""Get database URL."""
		return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

	@property
	def mcp_config(self) -> MCPConfig:
		"""Get MCP configuration."""
		return MCPConfig(
			server_url=self.MCP_SERVER_URL,
			api_key=self.MCP_API_KEY,
			default_model=self.MCP_DEFAULT_MODEL,
			timeout=self.MCP_TIMEOUT,
		)


settings = Settings()
