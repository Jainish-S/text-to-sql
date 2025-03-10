import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)

from text_to_sql.core.config import settings

logger = logging.getLogger(__name__)


engine = create_async_engine(
	settings.DATABASE_URL,
	echo=False,
	pool_size=settings.DB_MIN_CONNECTIONS,
	max_overflow=settings.DB_MAX_CONNECTIONS,
)

AsyncSessionFactory = async_sessionmaker(
	bind=engine,
	autoflush=False,
	expire_on_commit=False,
)


async def get_rds_session() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncSessionFactory() as session:
		yield session


async def close_db_pool() -> None:
	"""Close the database connection pool."""
	logger.info('Closing database connection pool')
	await engine.dispose()
