"""API data models."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class QueryRequest:
	"""Request for converting natural language to SQL."""

	query: str
	db_name: Optional[str] = None
	validate: bool = True


@dataclass
class QueryResponse:
	"""Response with generated SQL."""

	query: str
	sql: str
	validation: Optional[Dict] = None
	validation_failed: bool = False


@dataclass
class RefinementRequest:
	"""Request for refining a previously generated SQL."""

	query: str
	original_sql: str
	feedback: str
	db_name: Optional[str] = None


@dataclass
class RefinementResponse:
	"""Response with refined SQL."""

	query: str
	original_sql: str
	refined_sql: str
	changes: str
	validation: Optional[Dict] = None
	validation_failed: bool = False
