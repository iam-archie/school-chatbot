"""
School Textbook RAG System
==========================
RAG system for 6th Standard English Textbook with:
1. PDF Document Loading
2. Text Splitting & Chunking
3. Embedding & Vector Store (FAISS)
4. Corrective RAG (Context Quality Evaluation)
5. Fallback Mechanism (Multi-level Retrieval)
6. Guardrails Integration

Author: Sathish Suresh
Assignment: Social Eagle AI - Gen AI Architect Program
"""

import os
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from school_guardrails import SchoolStudentGuardrails, GuardrailResult


# ============================================================
# ENUMS
# ============================================================

class QualityLevel(Enum):
    """Context quality levels for Corrective RAG"""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class RetrievalLevel(Enum):
    """Fallback retrieval levels"""
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TERTIARY = "TERTIARY"
    FALLBACK = "FALLBACK"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ContextEvaluation:
    """Evaluation result for Corrective RAG"""
    relevance_score: float
    completeness_score: float
    clarity_score: float
    quality_level: QualityLevel
    needs_correction: bool
    reasoning: str


@dataclass
class RAGResponse:
    """Final response from the RAG system"""
    answer: str
    context_quality: QualityLevel
    retrieval_level: RetrievalLevel
    sources: List[str]
    was_corrected: bool
    guardrail_passed: bool
    confidence: str


# ============================================================
# MAIN CLASS
# ============================================================

class SchoolTextbookRAG:
    """
    RAG System for School Textbook with Corrective RAG and Fallback.
    
    Features:
    - PDF document loading
    - Corrective RAG (evaluates and improves retrieval)
    - Fallback mechanism (3 levels)
    - Guardrails for student safety
    """
    
    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small"
    ):
        """Initialize the RAG system."""
        self.openai_api_key = openai_api_key
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=openai_api_key
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            api_key=openai_api_key
        )
        
        # Text splitter for PDF
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        # Vector store
        self.vectorstore = None
        self.documents = []
        
        # Initialize Guardrails
        self.guardrails = SchoolStudentGuardrails()
        
        # System prompt for student-friendly responses
        self.system_prompt = """You are a friendly and helpful study assistant for 6th standard students.

Your role:
- Help students understand their English textbook lessons
- Explain concepts in simple, easy-to-understand language
- Be encouraging and supportive
- Use examples that students can relate to
- Keep responses brief but informative

Guidelines:
- Use simple words suitable for 6th grade students
- Be friendly and encouraging 😊
- If you don't know something, say "I'm not sure about that, but let's look at what we do know!"
- Always relate answers to the textbook content when possible

Remember: You're talking to young students, so be patient and kind!"""

        print("✅ School Textbook RAG System initialized")
    
    # ============================================================
    # DOCUMENT LOADING
    # ============================================================
    
    def load_pdf(self, pdf_path: str) -> int:
        """
        Load PDF document and create vector store.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of chunks created
        """
        print(f"📄 Loading PDF: {pdf_path}")
        
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
        except Exception as e:
            print(f"   ❌ Error loading PDF: {e}")
            return 0
        
        print(f"   📖 Loaded {len(pages)} pages")
        
        if not pages or len(pages) == 0:
            print("   ❌ No pages found in PDF!")
            return 0
        
        # Split into chunks - handle empty pages
        all_chunks = []
        pages_with_content = 0
        
        for i, page in enumerate(pages):
            try:
                # Skip empty pages
                page_content = page.page_content if hasattr(page, 'page_content') else ""
                
                if not page_content or not page_content.strip():
                    continue
                
                pages_with_content += 1
                
                # Split text with error handling
                try:
                    chunks = self.text_splitter.split_text(page_content)
                except Exception as split_error:
                    print(f"   ⚠️ Error splitting page {i+1}: {split_error}")
                    # Fallback: use the whole page as one chunk
                    chunks = [page_content.strip()] if page_content.strip() else []
                
                # Filter out empty chunks
                for j, chunk in enumerate(chunks):
                    if chunk and isinstance(chunk, str) and chunk.strip():
                        all_chunks.append(Document(
                            page_content=chunk.strip(),
                            metadata={
                                "source": pdf_path,
                                "page": i + 1,
                                "chunk_id": j
                            }
                        ))
            except Exception as page_error:
                print(f"   ⚠️ Error processing page {i+1}: {page_error}")
                continue
        
        print(f"   📄 Pages with content: {pages_with_content}")
        
        if not all_chunks or len(all_chunks) == 0:
            print("   ❌ No text content extracted from PDF!")
            print("   💡 The PDF might be image-based (scanned). Try a text-based PDF.")
            return 0
        
        self.documents = all_chunks
        print(f"   ✂️ Created {len(all_chunks)} chunks")
        
        # Create vector store
        print("   🔢 Creating embeddings...")
        try:
            self.vectorstore = FAISS.from_documents(
                documents=all_chunks,
                embedding=self.embeddings
            )
        except Exception as embed_error:
            print(f"   ❌ Error creating embeddings: {embed_error}")
            return 0
        
        print(f"✅ Vector store created with {len(all_chunks)} documents")
        return len(all_chunks)
    
    def load_text_documents(self, texts: List[str], source_name: str = "textbook") -> int:
        """
        Load text documents directly (for testing without PDF).
        
        Args:
            texts: List of text strings
            source_name: Name of the source
            
        Returns:
            Number of chunks created
        """
        all_chunks = []
        for i, text in enumerate(texts):
            chunks = self.text_splitter.split_text(text)
            for j, chunk in enumerate(chunks):
                all_chunks.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": source_name,
                        "section": i + 1,
                        "chunk_id": j
                    }
                ))
        
        self.documents = all_chunks
        
        # Create vector store
        self.vectorstore = FAISS.from_documents(
            documents=all_chunks,
            embedding=self.embeddings
        )
        
        print(f"✅ Loaded {len(texts)} documents → {len(all_chunks)} chunks")
        return len(all_chunks)
    
    # ============================================================
    # CORRECTIVE RAG - Context Evaluation
    # ============================================================
    
    def _evaluate_context(self, query: str, context: str) -> ContextEvaluation:
        """
        Evaluate the quality of retrieved context (Corrective RAG).
        
        Args:
            query: User's question
            context: Retrieved context
            
        Returns:
            ContextEvaluation with quality scores
        """
        # Handle empty context
        if not context or not context.strip():
            return ContextEvaluation(
                relevance_score=0.0,
                completeness_score=0.0,
                clarity_score=0.0,
                quality_level=QualityLevel.POOR,
                needs_correction=True,
                reasoning="No context retrieved"
            )
        
        evaluation_prompt = PromptTemplate(
            template="""Evaluate how well this context can answer the student's question.

STUDENT QUESTION: {query}

RETRIEVED CONTEXT:
{context}

Evaluate on 3 criteria (score 0.0 to 1.0):

1. RELEVANCE: How relevant is the context to the question?
2. COMPLETENESS: Does the context have enough information?
3. CLARITY: Is the context clear and understandable?

Respond in JSON:
{{
    "relevance_score": <0.0-1.0>,
    "completeness_score": <0.0-1.0>,
    "clarity_score": <0.0-1.0>,
    "reasoning": "<brief explanation>"
}}

JSON:""",
            input_variables=["query", "context"]
        )
        
        try:
            response = self.llm.invoke(evaluation_prompt.format(
                query=query,
                context=context[:2000]
            ))
            
            # Parse response
            response_text = response.content.strip()
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            scores = json.loads(response_text)
        except Exception as e:
            print(f"   ⚠️ Evaluation error: {e}")
            scores = {
                "relevance_score": 0.5,
                "completeness_score": 0.5,
                "clarity_score": 0.5,
                "reasoning": "Evaluation parsing failed"
            }
        
        # Calculate average and determine quality level
        avg_score = (
            scores.get("relevance_score", 0.5) + 
            scores.get("completeness_score", 0.5) + 
            scores.get("clarity_score", 0.5)
        ) / 3
        
        if avg_score >= 0.8:
            quality_level = QualityLevel.EXCELLENT
            needs_correction = False
        elif avg_score >= 0.6:
            quality_level = QualityLevel.GOOD
            needs_correction = False
        elif avg_score >= 0.4:
            quality_level = QualityLevel.FAIR
            needs_correction = True
        else:
            quality_level = QualityLevel.POOR
            needs_correction = True
        
        return ContextEvaluation(
            relevance_score=scores.get("relevance_score", 0.5),
            completeness_score=scores.get("completeness_score", 0.5),
            clarity_score=scores.get("clarity_score", 0.5),
            quality_level=quality_level,
            needs_correction=needs_correction,
            reasoning=scores.get("reasoning", "")
        )
    
    def _refine_query(self, original_query: str, evaluation: ContextEvaluation) -> str:
        """
        Refine query when context quality is poor (Corrective RAG).
        
        Args:
            original_query: Original student question
            evaluation: Context evaluation result
            
        Returns:
            Refined query string
        """
        refine_prompt = PromptTemplate(
            template="""The student's question didn't find good answers. Improve the search query.

ORIGINAL QUESTION: {query}

PROBLEM: {reasoning}

Create a better search query that:
- Uses keywords from the English textbook
- Is more specific
- Might find better matching content

Return ONLY the improved query (no explanation):

IMPROVED QUERY:""",
            input_variables=["query", "reasoning"]
        )
        
        response = self.llm.invoke(refine_prompt.format(
            query=original_query,
            reasoning=evaluation.reasoning
        ))
        
        return response.content.strip()
    
    # ============================================================
    # FALLBACK MECHANISM - Multi-level Retrieval
    # ============================================================
    
    def _retrieve_primary(self, query: str, k: int = 4) -> Tuple[List[Document], str]:
        """Level 1: Primary vector similarity search."""
        if not self.vectorstore:
            return [], ""
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            if not docs:
                return [], ""
            context = "\n\n".join([doc.page_content for doc in docs if doc.page_content])
            return docs, context
        except Exception as e:
            print(f"   ⚠️ Primary retrieval error: {e}")
            return [], ""
    
    def _retrieve_secondary(self, query: str, k: int = 6) -> Tuple[List[Document], str]:
        """Level 2: Keyword expansion search."""
        if not self.vectorstore:
            return [], ""
        
        try:
            # Expand query with educational keywords
            expanded_query = f"{query} lesson chapter story poem meaning"
            
            docs = self.vectorstore.similarity_search(expanded_query, k=k)
            if not docs:
                return [], ""
            context = "\n\n".join([doc.page_content for doc in docs if doc.page_content])
            return docs, context
        except Exception as e:
            print(f"   ⚠️ Secondary retrieval error: {e}")
            return [], ""
    
    def _retrieve_tertiary(self, query: str, k: int = 8) -> Tuple[List[Document], str]:
        """Level 3: Semantic expansion with LLM."""
        if not self.vectorstore:
            return [], ""
        
        try:
            # Use LLM to expand query
            expand_prompt = f"""Expand this student question with related educational terms:

Question: {query}

Add synonyms and related concepts for better textbook search.
Return only the expanded query:"""
            
            response = self.llm.invoke(expand_prompt)
            expanded_query = response.content.strip()
            
            docs = self.vectorstore.similarity_search(expanded_query, k=k)
            if not docs:
                return [], ""
            context = "\n\n".join([doc.page_content for doc in docs if doc.page_content])
            return docs, context
        except Exception as e:
            print(f"   ⚠️ Tertiary retrieval error: {e}")
            return [], ""
    
    # ============================================================
    # MAIN QUERY METHOD
    # ============================================================
    
    def query(self, user_query: str, verbose: bool = True) -> RAGResponse:
        """
        Main query method with Guardrails, Corrective RAG, and Fallback.
        
        Args:
            user_query: Student's question
            verbose: Print progress
            
        Returns:
            RAGResponse with answer and metadata
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"📚 Student Question: {user_query}")
            print('='*60)
        
        # ============================================================
        # STEP 1: INPUT GUARDRAILS
        # ============================================================
        if verbose:
            print("\n🛡️ Step 1: Checking Input Safety...")
        
        input_check = self.guardrails.validate_input(user_query)
        
        if not input_check.is_safe:
            if verbose:
                print(f"   🚫 BLOCKED: {input_check.blocked_category}")
            return RAGResponse(
                answer=input_check.reason,
                context_quality=QualityLevel.POOR,
                retrieval_level=RetrievalLevel.FALLBACK,
                sources=[],
                was_corrected=False,
                guardrail_passed=False,
                confidence="N/A"
            )
        
        if verbose:
            print("   ✅ Input is safe!")
        
        safe_query = input_check.sanitized_text
        
        # ============================================================
        # STEP 2: PRIMARY RETRIEVAL
        # ============================================================
        if verbose:
            print("\n📥 Step 2: Retrieving from Textbook (PRIMARY)...")
        
        docs, context = self._retrieve_primary(safe_query)
        retrieval_level = RetrievalLevel.PRIMARY
        
        if not docs:
            if verbose:
                print("   ❌ No documents found!")
            return RAGResponse(
                answer="I couldn't find information about that in your textbook. Could you try asking in a different way? 🤔",
                context_quality=QualityLevel.POOR,
                retrieval_level=RetrievalLevel.FALLBACK,
                sources=[],
                was_corrected=False,
                guardrail_passed=True,
                confidence="Low"
            )
        
        if verbose:
            print(f"   ✅ Found {len(docs)} relevant sections")
        
        # ============================================================
        # STEP 3: CORRECTIVE RAG - Evaluate Context Quality
        # ============================================================
        if verbose:
            print("\n🔍 Step 3: Evaluating Context Quality (CORRECTIVE RAG)...")
        
        evaluation = self._evaluate_context(safe_query, context)
        was_corrected = False
        
        if verbose:
            print(f"   📊 Relevance: {evaluation.relevance_score:.2f}")
            print(f"   📊 Completeness: {evaluation.completeness_score:.2f}")
            print(f"   📊 Clarity: {evaluation.clarity_score:.2f}")
            print(f"   📊 Quality Level: {evaluation.quality_level.value}")
        
        # ============================================================
        # STEP 4: FALLBACK MECHANISM (if needed)
        # ============================================================
        if evaluation.needs_correction:
            if verbose:
                print("\n🔄 Step 4: Applying Fallback Mechanism...")
            
            # Try SECONDARY retrieval
            if verbose:
                print("   📥 Trying SECONDARY retrieval (keyword expansion)...")
            docs, context = self._retrieve_secondary(safe_query)
            evaluation = self._evaluate_context(safe_query, context)
            retrieval_level = RetrievalLevel.SECONDARY
            
            if evaluation.needs_correction:
                # Try TERTIARY retrieval
                if verbose:
                    print("   📥 Trying TERTIARY retrieval (semantic expansion)...")
                
                # Also try query refinement (Corrective RAG)
                refined_query = self._refine_query(safe_query, evaluation)
                if verbose:
                    print(f"   🔧 Refined query: {refined_query}")
                
                docs, context = self._retrieve_tertiary(refined_query)
                evaluation = self._evaluate_context(refined_query, context)
                retrieval_level = RetrievalLevel.TERTIARY
                was_corrected = True
            
            if verbose:
                print(f"   ✅ Final Quality: {evaluation.quality_level.value}")
        
        # ============================================================
        # STEP 5: GENERATE RESPONSE
        # ============================================================
        if verbose:
            print("\n💬 Step 5: Generating Student-Friendly Response...")
        
        generation_prompt = PromptTemplate(
            template="""{system_prompt}

Based on the textbook content below, answer the student's question.

TEXTBOOK CONTENT:
{context}

STUDENT QUESTION: {query}

Remember:
- Use simple language for 6th grade students
- Be friendly and encouraging
- If the textbook doesn't have the answer, say so politely

YOUR ANSWER:""",
            input_variables=["system_prompt", "context", "query"]
        )
        
        response = self.llm.invoke(generation_prompt.format(
            system_prompt=self.system_prompt,
            context=context,
            query=safe_query
        ))
        
        answer = response.content
        
        # ============================================================
        # STEP 6: OUTPUT GUARDRAILS
        # ============================================================
        if verbose:
            print("\n🛡️ Step 6: Checking Output Safety...")
        
        output_check = self.guardrails.validate_output(answer)
        
        if not output_check.is_safe:
            if verbose:
                print(f"   🚫 Output blocked: {output_check.blocked_category}")
            answer = "I'm sorry, I couldn't generate an appropriate response. Please try asking another question! 😊"
        else:
            answer = output_check.sanitized_text
            if verbose:
                print("   ✅ Output is safe!")
        
        # Get sources
        sources = list(set([
            f"Page {doc.metadata.get('page', '?')}" 
            for doc in docs
        ]))
        
        # Determine confidence
        if evaluation.quality_level == QualityLevel.EXCELLENT:
            confidence = "High 🌟"
        elif evaluation.quality_level == QualityLevel.GOOD:
            confidence = "Good 👍"
        elif evaluation.quality_level == QualityLevel.FAIR:
            confidence = "Medium 🤔"
        else:
            confidence = "Low ❓"
        
        return RAGResponse(
            answer=answer,
            context_quality=evaluation.quality_level,
            retrieval_level=retrieval_level,
            sources=sources,
            was_corrected=was_corrected,
            guardrail_passed=True,
            confidence=confidence
        )
    
    def get_guardrail_metrics(self) -> Dict:
        """Get guardrail metrics."""
        return self.guardrails.get_metrics()
    
    def get_safety_report(self) -> str:
        """Get safety report."""
        return self.guardrails.get_safety_report()


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def create_school_rag(api_key: str = None) -> SchoolTextbookRAG:
    """Create SchoolTextbookRAG instance."""
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please provide api_key or set OPENAI_API_KEY")
    
    return SchoolTextbookRAG(openai_api_key=api_key)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY")
        exit()
    
    # Create RAG
    rag = SchoolTextbookRAG(openai_api_key=api_key)
    
    # Load sample content
    sample_texts = [
        """Chapter 1: The Giving Tree
        A young boy loved a tree. The tree gave him shade, apples to eat, 
        and branches to swing on. As the boy grew older, he needed more from 
        the tree. The tree gave everything - its apples, branches, and even 
        its trunk. The story teaches us about unconditional love and giving.""",
        
        """Chapter 2: New Words
        Vocabulary from The Giving Tree:
        - Shade: A dark area created when something blocks light
        - Branch: A part of a tree that grows from the trunk
        - Trunk: The main stem of a tree
        - Generous: Willing to give and share freely"""
    ]
    
    rag.load_text_documents(sample_texts, "English Textbook")
    
    # Test queries
    test_queries = [
        "What is the story about?",
        "What does shade mean?",
        "Tell me about sex",  # Should be blocked
        "How to cheat in exam",  # Should be blocked
    ]
    
    for query in test_queries:
        response = rag.query(query, verbose=True)
        print(f"\n📝 Answer: {response.answer}")
        print(f"📊 Quality: {response.context_quality.value}")
        print(f"🎯 Confidence: {response.confidence}")
    
    print("\n" + rag.get_safety_report())
