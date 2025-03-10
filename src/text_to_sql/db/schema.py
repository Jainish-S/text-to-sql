"""Database schema extraction and formatting using SQLAlchemy."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy import text

from text_to_sql.db.connection import AsyncSessionFactory

logger = logging.getLogger(__name__)


@dataclass
class Column:
	"""Database column information."""

	name: str
	data_type: str
	nullable: bool
	default: Optional[str] = None
	description: Optional[str] = None


@dataclass
class Table:
	"""Representation of a database table."""

	name: str
	schema: str
	columns: List[Column] = field(default_factory=list)
	description: Optional[str] = None

	def __str__(self) -> str:
		"""String representation of the table."""
		column_info = '\n  '.join([f'{col.name} {col.data_type}' for col in self.columns])
		return f'Table: {self.schema}.{self.name}\n  {column_info}'

	def to_dict(self) -> Dict:
		"""Convert to dictionary representation."""
		return {
			'name': self.name,
			'schema': self.schema,
			'description': self.description,
			'columns': [
				{
					'name': col.name,
					'type': col.data_type,
					'nullable': col.nullable,
					'default': col.default,
					'description': col.description,
				}
				for col in self.columns
			],
		}


@dataclass
class ForeignKey:
	"""Foreign key relationship."""

	table_schema: str
	table_name: str
	column_name: str
	foreign_table_schema: str
	foreign_table_name: str
	foreign_column_name: str


@dataclass
class DatabaseSchema:
	"""Complete database schema with tables and relationships."""

	tables: List[Table] = field(default_factory=list)
	foreign_keys: List[ForeignKey] = field(default_factory=list)

	def to_dict(self) -> Dict:
		"""Convert schema to dictionary."""
		return {
			'tables': [table.to_dict() for table in self.tables],
			'foreign_keys': [
				{
					'table': f'{fk.table_schema}.{fk.table_name}',
					'column': fk.column_name,
					'references': f'{fk.foreign_table_schema}.{fk.foreign_table_name}',
					'referenced_column': fk.foreign_column_name,
				}
				for fk in self.foreign_keys
			],
		}

	def to_context_string(self) -> str:
		"""Format schema as a context string for the LLM."""
		result = ['DATABASE SCHEMA:']

		# Add tables
		for table in self.tables:
			table_info = [f'Table: {table.schema}.{table.name}']
			if table.description:
				table_info.append(f'Description: {table.description}')

			# Add columns
			table_info.append('Columns:')
			for col in table.columns:
				col_info = f'  - {col.name} ({col.data_type})'
				if not col.nullable:
					col_info += ' NOT NULL'
				if col.default:
					col_info += f' DEFAULT {col.default}'
				if col.description:
					col_info += f' -- {col.description}'
				table_info.append(col_info)

			result.append('\n'.join(table_info))

		# Add foreign keys
		if self.foreign_keys:
			result.append('FOREIGN KEYS:')
			for fk in self.foreign_keys:
				result.append(
					f'  - {fk.table_schema}.{fk.table_name}.{fk.column_name} → '
					f'{fk.foreign_table_schema}.{fk.foreign_table_name}.{fk.foreign_column_name}'
				)

		return '\n\n'.join(result)


async def extract_schema(db_name: Optional[str] = None) -> DatabaseSchema:
	"""Extract schema information from the database."""
	tables = []
	foreign_keys = []

	async with AsyncSessionFactory() as session:
		# Query for all tables in the database
		result = await session.execute(
			text("""
            SELECT 
                t.table_schema, 
                t.table_name,
                obj_description(pgc.oid) as table_description
            FROM 
                information_schema.tables t
            JOIN 
                pg_catalog.pg_class pgc ON t.table_name = pgc.relname
            JOIN
                pg_catalog.pg_namespace pgn ON pgc.relnamespace = pgn.oid AND t.table_schema = pgn.nspname
            WHERE 
                t.table_type = 'BASE TABLE' 
                AND t.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY 
                t.table_schema, t.table_name
            """)
		)

		table_rows = result.fetchall()

		for table_row in table_rows:
			schema_name = table_row.table_schema
			table_name = table_row.table_name
			description = table_row.table_description

			# Now fetch columns for this table
			col_result = await session.execute(
				text("""
                SELECT 
                    c.column_name, 
                    c.data_type, 
                    c.column_default,
                    c.is_nullable,
                    col_description(pgc.oid, c.ordinal_position) as column_description
                FROM 
                    information_schema.columns c
                JOIN 
                    pg_catalog.pg_class pgc ON c.table_name = pgc.relname
                JOIN
                    pg_catalog.pg_namespace pgn ON pgc.relnamespace = pgn.oid AND c.table_schema = pgn.nspname
                WHERE 
                    c.table_schema = :schema 
                    AND c.table_name = :table
                ORDER BY 
                    c.ordinal_position
                """),
				{'schema': schema_name, 'table': table_name},
			)

			columns = []
			for col_row in col_result.fetchall():
				columns.append(
					Column(
						name=col_row.column_name,
						data_type=col_row.data_type,
						default=col_row.column_default,
						nullable=col_row.is_nullable == 'YES',
						description=col_row.column_description,
					)
				)

			table = Table(name=table_name, schema=schema_name, description=description, columns=columns)
			tables.append(table)

		# Fetch foreign key relationships
		fk_result = await session.execute(
			text("""
            SELECT
                kcu.table_schema,
                kcu.table_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
            JOIN
                information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN
                information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE
                tc.constraint_type = 'FOREIGN KEY'
            ORDER BY
                kcu.table_schema,
                kcu.table_name
            """)
		)

		for fk_row in fk_result.fetchall():
			foreign_keys.append(
				ForeignKey(
					table_schema=fk_row.table_schema,
					table_name=fk_row.table_name,
					column_name=fk_row.column_name,
					foreign_table_schema=fk_row.foreign_table_schema,
					foreign_table_name=fk_row.foreign_table_name,
					foreign_column_name=fk_row.foreign_column_name,
				)
			)

	return DatabaseSchema(tables=tables, foreign_keys=foreign_keys)
