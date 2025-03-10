"""Database schema caching mechanism."""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from text_to_sql.core.config import settings
from text_to_sql.db.schema import DatabaseSchema, extract_schema

logger = logging.getLogger(__name__)


@dataclass
class CachedSchema:
	"""Cached schema with timestamp."""

	schema: DatabaseSchema
	timestamp: float


_schema_cache: Dict[str, CachedSchema] = {}


async def get_schema_context(db_name: Optional[str] = None, db_session: Optional[AsyncSession] = None) -> str:
	"""Get the schema context string for the given database."""
	schema = await get_cached_schema(db_name, db_session)
	return schema.to_context_string()


async def get_cached_schema(db_name: Optional[str] = None, db_session: Optional[AsyncSession] = None) -> DatabaseSchema:
	"""Get the cached schema, refreshing if necessary."""
	cache_key = db_name or 'default'

	if cache_key in _schema_cache:
		cached = _schema_cache[cache_key]
		age = time.time() - cached.timestamp

		if age < settings.SCHEMA_CACHE_TTL:
			logger.debug(f'Using cached schema for {cache_key}, age: {age:.1f}s')
			return cached.schema

	logger.info(f'Refreshing schema cache for {cache_key}')
	schema = await extract_schema(db_name)
	_schema_cache[cache_key] = CachedSchema(schema=schema, timestamp=time.time())

	return schema


async def invalidate_schema_cache(db_name: Optional[str] = None) -> None:
	"""Invalidate the schema cache for the given database."""
	if db_name is None:
		logger.info('Invalidating all schema caches')
		_schema_cache.clear()
	else:
		logger.info(f'Invalidating schema cache for {db_name}')
		if db_name in _schema_cache:
			del _schema_cache[db_name]
