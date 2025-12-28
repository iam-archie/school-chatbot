"""
School Textbook Chatbot
=======================
A safe educational chatbot for 6th Standard students.

Features:
- PDF textbook loading
- Corrective RAG (context quality evaluation)
- Fallback mechanism (multi-level retrieval)
- Guardrails (student safety protection)
- Streamlit UI

Usage:
    # Run the Streamlit app
    streamlit run app.py
    
    # Or use programmatically
    from school_rag import SchoolTextbookRAG
    
    rag = SchoolTextbookRAG(openai_api_key="sk-xxx")
    rag.load_pdf("textbook.pdf")
    response = rag.query("What is the story about?")
    print(response.answer)

Author: Sathish Suresh
Assignment: Social Eagle AI - Gen AI Architect Program
"""

from .school_guardrails import SchoolStudentGuardrails, GuardrailResult
from .school_rag import SchoolTextbookRAG, QualityLevel, RetrievalLevel, RAGResponse

__all__ = [
    "SchoolStudentGuardrails",
    "GuardrailResult",
    "SchoolTextbookRAG",
    "QualityLevel",
    "RetrievalLevel",
    "RAGResponse"
]

__version__ = "1.0.0"
__author__ = "Sathish Suresh"
