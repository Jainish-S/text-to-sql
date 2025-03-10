"""FastAPI application setup."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from text_to_sql.api.routes.query import router as query_router
from text_to_sql.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Application lifecycle events handler."""
	# Startup event
	logger.info('Starting Text-to-SQL API server')

	yield

	# Shutdown event
	from text_to_sql.db.connection import close_db_pool

	logger.info('Shutting down Text-to-SQL API server')
	await close_db_pool()


app = FastAPI(
	title='Text-to-SQL API', description='Convert natural language to SQL queries using LLMs', version='0.1.0', lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

app.include_router(query_router, prefix='/api/v1', tags=['SQL Generation'])


@app.get('/health')
async def health_check():
	"""Health check endpoint."""
	from text_to_sql.db.connection import test_connection

	db_status, db_error = await test_connection()

	return {
		'status': 'healthy' if db_status else 'unhealthy',
		'database': 'connected' if db_status else f'error: {db_error}',
		'version': '0.1.0',
	}
