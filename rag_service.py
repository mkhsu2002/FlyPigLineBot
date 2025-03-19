import os
import logging
import numpy as np
import faiss
import pickle
from flask import current_app
from config import is_rag_enabled
from services.llm_service import LLMService
from app import db

# 延遲導入模型函數
def get_document_model():
    """獲取 Document 模型"""
    from app import Document
    return Document

logger = logging.getLogger(__name__)

class RAGService:
    """Service for Retrieval Augmented Generation (RAG)"""
    
    # Path for storing the FAISS index
    INDEX_PATH = "knowledge_base/faiss_index.idx"
    EMBEDDINGS_PATH = "knowledge_base/embeddings.pkl"
    
    @staticmethod
    def get_embedding(text, client=None):
        """Get embedding for a text using OpenAI API"""
        if client is None:
            client = LLMService.get_client()
            if not client:
                logger.error("Failed to initialize OpenAI client for embeddings")
                return None
        
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    @staticmethod
    def initialize_index():
        """Initialize or load the FAISS index"""
        # Create knowledge_base directory if it doesn't exist
        os.makedirs("knowledge_base", exist_ok=True)
        
        # Check if index already exists
        if os.path.exists(RAGService.INDEX_PATH) and os.path.exists(RAGService.EMBEDDINGS_PATH):
            try:
                # Load existing index
                index = faiss.read_index(RAGService.INDEX_PATH)
                with open(RAGService.EMBEDDINGS_PATH, 'rb') as f:
                    doc_embeddings = pickle.load(f)
                logger.info("Loaded existing FAISS index")
                return index, doc_embeddings
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
        
        # Create new index
        logger.info("Creating new FAISS index")
        embedding_dim = 1536  # OpenAI's text-embedding-3-small dimension
        index = faiss.IndexFlatL2(embedding_dim)
        doc_embeddings = {}
        
        return index, doc_embeddings
    
    @staticmethod
    def update_index():
        """Update the FAISS index with all documents in the database"""
        client = LLMService.get_client()
        if not client:
            logger.error("Cannot update index: OpenAI client initialization failed")
            return False
            
        try:
            # Initialize index
            index, doc_embeddings = RAGService.initialize_index()
            
            # Get all active documents
            Document = get_document_model()
            documents = Document.query.filter_by(is_active=True).all()
            
            # Reset index
            if index.ntotal > 0:
                index.reset()
                doc_embeddings = {}
            
            # 分批處理文件，避免記憶體溢出
            batch_size = 5  # 每批處理的文件數量
            total_docs = len(documents)
            processed_docs = 0
            
            for i in range(0, total_docs, batch_size):
                batch_docs = documents[i:i+batch_size]
                # Generate embeddings for documents in this batch
                for doc in batch_docs:
                    try:
                        # 設置重試機制
                        max_retries = 3
                        retry_delay = 1
                        embedding = None
                        
                        for attempt in range(max_retries):
                            try:
                                embedding = RAGService.get_embedding(doc.content, client)
                                if embedding:
                                    break
                                
                                if attempt < max_retries - 1:
                                    import time
                                    time.sleep(retry_delay)
                                    retry_delay *= 2
                            except Exception as retry_error:
                                logger.warning(f"Retry {attempt+1}/{max_retries} failed for document {doc.id}: {retry_error}")
                                if attempt < max_retries - 1:
                                    import time
                                    time.sleep(retry_delay)
                                    retry_delay *= 2
                        
                        if embedding:
                            # Convert to numpy array and reshape
                            embedding_np = np.array(embedding).astype('float32').reshape(1, -1)
                            
                            # Add to index
                            index.add(embedding_np)
                            
                            # 僅保存必要的摘要信息，節省記憶體
                            content_preview = doc.content[:500] if len(doc.content) > 500 else doc.content
                            doc_embeddings[index.ntotal - 1] = {
                                "id": doc.id,
                                "title": doc.title,
                                "content": content_preview
                            }
                            processed_docs += 1
                    except Exception as doc_error:
                        logger.error(f"Error processing document {doc.id}: {doc_error}")
                        continue
                
                # 每批處理完成后保存一次索引，確保進度不丟失
                if i + batch_size >= total_docs or (i > 0 and i % (batch_size * 3) == 0):
                    faiss.write_index(index, RAGService.INDEX_PATH)
                    with open(RAGService.EMBEDDINGS_PATH, 'wb') as f:
                        pickle.dump(doc_embeddings, f)
                    logger.info(f"Interim save: Processed {processed_docs}/{total_docs} documents")
            
            # 最終保存索引
            faiss.write_index(index, RAGService.INDEX_PATH)
            with open(RAGService.EMBEDDINGS_PATH, 'wb') as f:
                pickle.dump(doc_embeddings, f)
                
            logger.info(f"Updated FAISS index with {processed_docs}/{total_docs} documents")
            return True
        except Exception as e:
            logger.error(f"Error updating FAISS index: {e}")
            return False
    
    @staticmethod
    def search(query, top_k=3):
        """Search the FAISS index for relevant documents"""
        if not is_rag_enabled():
            logger.info("RAG is disabled, skipping search")
            return None
            
        client = LLMService.get_client()
        if not client:
            logger.error("Cannot search: OpenAI client initialization failed")
            return None
            
        try:
            # Get embedding for query
            query_embedding = RAGService.get_embedding(query, client)
            if not query_embedding:
                return None
                
            query_np = np.array(query_embedding).astype('float32').reshape(1, -1)
            
            # Load index
            index, doc_embeddings = RAGService.initialize_index()
            
            # If index is empty, no results
            if index.ntotal == 0:
                return None
                
            # Search index
            distances, indices = index.search(query_np, min(top_k, index.ntotal))
            
            # Get results
            results = []
            for idx in indices[0]:
                if idx in doc_embeddings:
                    results.append(doc_embeddings[idx])
            
            return results
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return None
    
    @staticmethod
    def get_context_for_query(query):
        """Get context from knowledge base for a query"""
        if not is_rag_enabled():
            return None
            
        results = RAGService.search(query)
        if not results:
            return None
            
        # Combine results into a context string
        context = "Knowledge base information:\n\n"
        for i, result in enumerate(results):
            context += f"{i+1}. {result['title']}:\n{result['content']}\n\n"
            
        return context
    
    @staticmethod
    def add_document(title, content, filename=None):
        """Add a document to the database and update the index"""
        try:
            # Get Document model and add to database
            Document = get_document_model()
            doc = Document(
                title=title,
                content=content,
                filename=filename,
                is_active=True
            )

            db.session.add(doc)
            db.session.commit()
            
            # Update index
            RAGService.update_index()
            
            return True, doc.id
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            db.session.rollback()
            return False, str(e)
            
    @staticmethod
    def export_knowledge_base():
        """Export all knowledge base documents as a downloadable file"""
        try:
            Document = get_document_model()
            documents = Document.query.all()
            
            # Create a formatted text file with all documents
            export_content = "# FlyPig 知識庫匯出\n\n"
            
            for i, doc in enumerate(documents, 1):
                export_content += f"## {i}. {doc.title}\n"
                if doc.filename:
                    export_content += f"來源: {doc.filename}\n"
                export_content += f"上傳時間: {doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                export_content += f"{doc.content}\n\n"
                export_content += "---\n\n"
            
            return export_content
        except Exception as e:
            logger.error(f"Error exporting knowledge base: {e}")
            return None
    
    @staticmethod
    def delete_document(doc_id):
        """Delete a document from the database and update the index"""
        try:
            Document = get_document_model()
            doc = Document.query.get(doc_id)
            if not doc:
                return False, "Document not found"
                
            db.session.delete(doc)
            db.session.commit()
            
            # Update index
            RAGService.update_index()
            
            return True, "Document deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            db.session.rollback()
            return False, str(e)
