# chains/db_summary_chain.py
from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from ..prompts.db_summary_prompt import DB_SUMMARY_PROMPT_TEMPLATE

def build_db_summary_messages(*, question: str, query: str, params: dict, rows_json: str):
    prompt = ChatPromptTemplate.from_template(DB_SUMMARY_PROMPT_TEMPLATE)
    return prompt.format_messages(
        question=question,
        query=query,
        params=params,
        rows_json=rows_json,
    )
