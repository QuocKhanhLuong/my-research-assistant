"""
RAG (Retrieval-Augmented Generation) Service.
Business logic for PDF ingestion, embedding, and question answering.

Uses LangChain v1.x LCEL (LangChain Expression Language) for chains.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.core.config import Settings, get_settings

# Configure logging
logger = logging.getLogger(__name__)


def format_docs(docs: List[Any]) -> str:
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)


class RAGService:
    """
    RAG Service for PDF-based question answering.
    
    Handles:
    - PDF document loading and processing
    - Text chunking and embedding
    - Vector store management (FAISS)
    - Question answering with LLM using LCEL chains
    """
    
    # Vietnamese-optimized prompt template
    SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên về quy chế thi và kiểm tra.
Hãy trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.
Nếu không tìm thấy thông tin trong ngữ cảnh, hãy nói rằng bạn không có thông tin về vấn đề này.
Trả lời bằng tiếng Việt một cách rõ ràng và chính xác."""

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize RAG Service.
        
        Args:
            settings: Application settings. If None, uses default settings.
        """
        self.settings = settings or get_settings()
        
        self.pdf_directory = self.settings.get_absolute_pdf_directory()
        self.index_path = self.settings.get_absolute_index_path()
        
        self.vectorstore: Optional[FAISS] = None
        self.rag_chain: Optional[Any] = None
        self.documents: List[Any] = []
        self._last_retrieved_docs: List[Any] = []
        
        self._embeddings: Optional[FastEmbedEmbeddings] = None
        self._llm: Optional[ChatOpenAI] = None
        
        logger.info(f"RAGService initialized with PDF dir: {self.pdf_directory}")
        logger.info(f"FAISS index path: {self.index_path}")
    
    @property
    def embeddings(self) -> FastEmbedEmbeddings:
        """Lazy-loaded embeddings model."""
        if self._embeddings is None:
            logger.info(f"Loading embedding model: {self.settings.embedding_model}")
            self._embeddings = FastEmbedEmbeddings(
                model_name=self.settings.embedding_model
            )
        return self._embeddings
    
    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-loaded LLM instance."""
        if self._llm is None:
            logger.info(f"Initializing LLM: {self.settings.llm_model}")
            self._llm = ChatOpenAI(
                model=self.settings.llm_model,
                api_key=self.settings.megallm_api_key,
                base_url=self.settings.megallm_base_url,
                temperature=self.settings.llm_temperature,
            )
        return self._llm
    
    def load_pdfs(self) -> List[Any]:
        """
        Load all PDF files from the configured directory.
        
        Returns:
            List of loaded documents.
        
        Raises:
            FileNotFoundError: If PDF directory doesn't exist.
        """
        if not os.path.exists(self.pdf_directory):
            raise FileNotFoundError(f"PDF directory not found: {self.pdf_directory}")
        
        pdf_files = [f for f in os.listdir(self.pdf_directory) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.pdf_directory}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        documents = []
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.pdf_directory, pdf_file)
            try:
                loader = PyPDFLoader(pdf_path)
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} pages from {pdf_file}")
            except Exception as e:
                logger.error(f"Error loading {pdf_file}: {e}")
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents
    
    def split_documents(self, documents: List[Any]) -> List[Any]:
        """
        Split documents into chunks for embedding.
        
        Args:
            documents: List of documents to split.
            
        Returns:
            List of document chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        return chunks
    
    def build_vectorstore(self, chunks: List[Any]) -> FAISS:
        """
        Build FAISS vector store from document chunks.
        
        Args:
            chunks: List of document chunks to embed.
            
        Returns:
            FAISS vector store instance.
        """
        logger.info("Building FAISS vector store...")
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # Save to disk
        vectorstore.save_local(self.index_path)
        logger.info(f"Vector store saved to {self.index_path}")
        
        return vectorstore
    
    def load_vectorstore(self) -> Optional[FAISS]:
        """
        Load existing FAISS vector store from disk.
        
        Returns:
            FAISS vector store instance, or None if not found.
        """
        if not os.path.exists(self.index_path):
            logger.info("No existing vector store found")
            return None
        
        try:
            logger.info(f"Loading vector store from {self.index_path}")
            vectorstore = FAISS.load_local(
                self.index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Vector store loaded successfully")
            return vectorstore
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return None
    
    def initialize(self, force_rebuild: bool = False) -> bool:
        """
        Initialize the RAG service.
        
        Loads or builds the vector store and sets up the RAG chain.
        
        Args:
            force_rebuild: If True, rebuilds index even if it exists.
            
        Returns:
            True if initialization successful, False otherwise.
        """
        try:
            # Try to load existing index
            if not force_rebuild:
                self.vectorstore = self.load_vectorstore()
            
            # Build new index if needed
            if self.vectorstore is None:
                logger.info("Building new vector store...")
                documents = self.load_pdfs()
                
                if not documents:
                    logger.error("No documents to process")
                    return False
                
                chunks = self.split_documents(documents)
                self.documents = chunks
                self.vectorstore = self.build_vectorstore(chunks)
            
            # Setup RAG chain with LCEL
            self._setup_rag_chain()
            
            logger.info("RAG Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            return False
    
    def _setup_rag_chain(self) -> None:
        """Configure the RAG chain using LCEL (LangChain Expression Language)."""
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized")
        
        # Create retriever
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": self.settings.retrieval_k}
        )
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", """Ngữ cảnh:
{context}

Câu hỏi: {question}

Trả lời:"""),
        ])
        
        # Store retrieved docs for source tracking
        def retrieve_and_store(query: str) -> str:
            docs = retriever.invoke(query)
            self._last_retrieved_docs = docs
            return format_docs(docs)
        
        # Build LCEL chain
        self.rag_chain = (
            {"context": retrieve_and_store, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Store retriever for similarity search
        self._retriever = retriever
        
        logger.info("RAG chain configured with LCEL")
    
    def get_answer(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get answer for a query using RAG.
        
        Args:
            query: User's question.
            
        Returns:
            Tuple of (answer_text, list_of_sources)
            
        Raises:
            ValueError: If service not initialized.
        """
        if self.rag_chain is None:
            raise ValueError("RAG service not initialized. Call initialize() first.")
        
        logger.info(f"Processing query: {query[:50]}...")
        
        # Run the chain
        answer = self.rag_chain.invoke(query)
        
        # Get sources from stored docs
        sources = []
        for doc in self._last_retrieved_docs:
            sources.append({
                "content": doc.page_content[:500],  # Limit content length
                "page": doc.metadata.get("page", 0),
                "source": os.path.basename(doc.metadata.get("source", "unknown"))
            })
        
        logger.info(f"Generated answer with {len(sources)} sources")
        return answer, sources
    
    def search_similar(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Search for similar documents without generating an answer.
        
        Args:
            query: Search query.
            k: Number of results to return.
            
        Returns:
            List of similar document chunks.
            
        Raises:
            ValueError: If service not initialized.
        """
        if self.vectorstore is None:
            raise ValueError("RAG service not initialized. Call initialize() first.")
        
        docs = self.vectorstore.similarity_search(query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "page": doc.metadata.get("page", 0),
                "source": os.path.basename(doc.metadata.get("source", "unknown"))
            })
        
        return results
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is properly initialized."""
        return self.vectorstore is not None and self.rag_chain is not None
    
    @property
    def num_documents(self) -> int:
        """Get number of documents in vector store."""
        if self.vectorstore is None:
            return 0
        try:
            return self.vectorstore.index.ntotal
        except Exception:
            return len(self.documents) if self.documents else 0


# Singleton instance for dependency injection
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get or create RAG service singleton.
    
    Returns:
        RAGService instance.
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


async def initialize_rag_service() -> RAGService:
    """
    Initialize RAG service (for startup event).
    
    Returns:
        Initialized RAGService instance.
    """
    service = get_rag_service()
    service.initialize()
    return service
