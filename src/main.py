"""Application entry point."""

import argparse
import asyncio
import logging
import sys

import uvicorn

from text_to_sql.core.config import settings
from text_to_sql.db.connection import test_connection


def configure_logging(log_level: str = 'INFO'):
	"""Configure logging settings."""
	numeric_level = getattr(logging, log_level.upper(), None)
	if not isinstance(numeric_level, int):
		raise ValueError(f'Invalid log level: {log_level}')

	logging.basicConfig(
		level=numeric_level,
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
	)


def parse_args():
	"""Parse command line arguments."""
	parser = argparse.ArgumentParser(description='Text-to-SQL API server')
	parser.add_argument('--host', type=str, default=settings.API_HOST, help='Host IP to bind')
	parser.add_argument('--port', type=int, default=settings.API_PORT, help='Port to bind')
	parser.add_argument(
		'--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level'
	)
	parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')

	return parser.parse_args()


async def check_database():
	"""Test database connection."""
	success, error = await test_connection()
	if not success:
		logging.error(f'Failed to connect to database: {error}')
		sys.exit(1)
	return True


def main():
	"""Application main entry point."""
	args = parse_args()

	# Configure logging
	configure_logging(args.log_level)

	# Check database connection (async)
	asyncio.run(check_database())

	# Start server
	logging.info(f'Starting Text-to-SQL server on {args.host}:{args.port}')
	uvicorn.run('text_to_sql.api.app:app', host=args.host, port=args.port, reload=args.reload, log_level=args.log_level.lower())


if __name__ == '__main__':
	main()
