"""REST API routes for text-to-SQL conversions."""

import logging

from fastapi import APIRouter, Body, HTTPException

from text_to_sql.api.models.api_models import (
	QueryRequest,
	QueryResponse,
	RefinementRequest,
	RefinementResponse,
)
from text_to_sql.sql.generator import SQLGenerator
from text_to_sql.sql.refiner import QueryRefiner

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/query', response_model=QueryResponse)
async def generate_sql_query(
	request: QueryRequest = Body(...),
):
	"""Convert natural language to SQL query."""
	try:
		generator = SQLGenerator()
		result = await generator.generate_sql(
			natural_language_query=request.query, db_name=request.db_name, validate=request.validate
		)

		return QueryResponse(
			query=result.query, sql=result.sql, validation=result.validation, validation_failed=result.validation_failed
		)
	except Exception as e:
		logger.error(f'Error generating SQL query: {e}')
		raise HTTPException(status_code=500, detail=str(e))


@router.post('/refine', response_model=RefinementResponse)
async def refine_sql_query(
	request: RefinementRequest = Body(...),
):
	"""Refine a previously generated SQL query based on feedback."""
	try:
		refiner = QueryRefiner()
		result = await refiner.refine_query(
			original_query=request.query,
			original_sql=request.original_sql,
			feedback=request.feedback,
			db_name=request.db_name,
		)

		return RefinementResponse(
			query=request.query,
			original_sql=request.original_sql,
			refined_sql=result.refined_sql,
			changes=result.changes,
			validation=result.validation,
			validation_failed=result.validation_failed,
		)
	except Exception as e:
		logger.error(f'Error refining SQL query: {e}')
		raise HTTPException(status_code=500, detail=str(e))
