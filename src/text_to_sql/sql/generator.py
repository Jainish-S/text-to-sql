"""SQL generation pipeline."""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from text_to_sql.db.cache import get_schema_context
from text_to_sql.mcp.client import MCPClient
from text_to_sql.sql.validator import validate_sql

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
	"""Result of SQL generation."""

	query: str
	sql: str
	validation: Optional[Dict] = None
	validation_failed: bool = False


class SQLGenerator:
	"""SQL generation pipeline."""

	def __init__(self, mcp_client: Optional[MCPClient] = None):
		"""Initialize the SQL generator."""
		self.mcp_client = mcp_client or MCPClient()

	async def generate_sql(
		self,
		natural_language_query: str,
		db_name: Optional[str] = None,
		validate: bool = True,
		db_session: Optional[AsyncSession] = None,
	) -> GenerationResult:
		"""Generate SQL from natural language."""
		# Get schema context
		schema_context = await get_schema_context(db_name, db_session)

		# Generate SQL
		logger.info(f'Generating SQL for query: {natural_language_query}')
		sql = await self.mcp_client.generate_sql(
			natural_language_query=natural_language_query,
			schema_context=schema_context,
		)

		result = GenerationResult(
			query=natural_language_query,
			sql=sql,
		)

		# Validate if requested
		if validate:
			logger.debug(f'Validating SQL: {sql}')
			validation_result = await validate_sql(sql, schema_context, db_session)
			result.validation = validation_result

			# If validation failed, include error information
			if not validation_result.get('is_valid', False):
				logger.warning(f'SQL validation failed: {validation_result.get("issues")}')
				result.validation_failed = True

		return result
