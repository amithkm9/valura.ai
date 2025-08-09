"""
Advanced RAG Implementation for ADGM Corporate Agent
Implements hybrid search, query expansion, re-ranking, and chain-of-thought reasoning
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import ollama
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder
import re
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Document chunk with metadata"""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[np.ndarray] = None
    score: float = 0.0

class AdvancedRAG:
    """Advanced RAG system with hybrid search and re-ranking"""
    
    def __init__(self, model_name: str = "llama2"):
        self.model_name = model_name
        
        # Initialize embedding models
        logger.info("Initializing embedding models...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Initialize Ollama client
        self.ollama_client = ollama.Client()
        
        # Initialize ChromaDB with persistence
        logger.info("Initializing vector database...")
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Create collections for different document types
        self.collections = {}
        self._initialize_collections()
        
        # Query cache for performance
        self.query_cache = {}
        
        # Load ADGM knowledge base
        self._load_knowledge_base()
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections for different document types"""
        collection_names = [
            "adgm_regulations",
            "document_templates", 
            "compliance_rules",
            "legal_precedents"
        ]
        
        for name in collection_names:
            try:
                self.collections[name] = self.chroma_client.create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created collection: {name}")
            except:
                self.collections[name] = self.chroma_client.get_collection(name)
                logger.info(f"Loaded existing collection: {name}")
    
    def _load_knowledge_base(self):
        """Load ADGM regulations and rules into vector database"""
        
        logger.info("Loading ADGM knowledge base...")
        
        # ADGM Regulations
        regulations = [
            {
                "id": "reg_companies_2020",
                "content": """ADGM Companies Regulations 2020 - Key Requirements:
                Article 6: Jurisdiction - All companies must explicitly specify Abu Dhabi Global Market (ADGM) as their jurisdiction. References to UAE Federal Courts, Dubai Courts, or other jurisdictions are non-compliant.
                Article 12: Share Capital - Articles of Association must include clear statement of authorized share capital in specific currency (USD, AED, GBP, EUR).
                Article 15: Directors - Minimum one director required who must be a natural person of at least 18 years of age. Body corporate directors are permitted as additional directors.
                Article 20: Resolutions - All shareholder and board resolutions require proper signatures, dates, and clear resolution language using "RESOLVED" or "IT WAS RESOLVED".
                Article 25: Registered Office - Every company must maintain a registered office within ADGM jurisdiction at all times.
                Article 30: Company Name - Must include appropriate suffix (Limited, Ltd, LLC, etc.) and be unique within ADGM registry.""",
                "type": "regulation",
                "source": "ADGM Companies Regulations 2020",
                "year": 2020
            },
            {
                "id": "reg_employment_2019", 
                "content": """ADGM Employment Regulations 2019:
                Article 5: Employment Contracts - All employment contracts must comply with ADGM labor laws and include: job title, duties, salary, working hours, leave entitlements, notice periods.
                Article 10: Notice Periods - Minimum notice periods: 1 week for employment less than 3 months, 2 weeks for 3-12 months, 4 weeks for over 12 months.
                Article 15: Working Hours - Maximum 48 hours per week unless opt-out agreement signed.
                Article 20: Annual Leave - Minimum 20 days annual leave plus ADGM public holidays.""",
                "type": "regulation",
                "source": "ADGM Employment Regulations 2019",
                "year": 2019
            },
            {
                "id": "reg_data_protection_2021",
                "content": """ADGM Data Protection Regulations 2021:
                Article 8: Data Processing - Requires lawful basis for processing personal data.
                Article 15: Data Subject Rights - Rights include access, rectification, erasure, portability.
                Article 25: Data Breach Notification - 72-hour notification requirement for breaches.
                Article 30: Data Protection Officer - Required for certain organizations.""",
                "type": "regulation",
                "source": "ADGM Data Protection Regulations 2021",
                "year": 2021
            }
        ]
        
        # Document templates and requirements
        templates = [
            {
                "id": "template_aoa",
                "content": """Articles of Association Template Requirements:
                1. Company Name and Suffix - Must include Ltd, Limited, LLC, or Inc.
                2. Registered Office - Full ADGM address required
                3. Objects Clause - Detailed business activities
                4. Share Capital - Authorized and issued amounts
                5. Share Classes - Rights and restrictions
                6. Directors - Powers, appointment, removal procedures
                7. Shareholders - Rights, meetings, voting procedures
                8. Dividends - Declaration and payment procedures
                9. Accounts - Financial year, audit requirements
                10. Winding Up - Procedures for dissolution
                11. Governing Law - ADGM laws and regulations
                12. Dispute Resolution - ADGM Courts jurisdiction""",
                "type": "template",
                "document_type": "articles_of_association"
            },
            {
                "id": "template_board_resolution",
                "content": """Board Resolution Template Requirements:
                1. Company Name and Registration Number
                2. Date, Time, and Venue of Meeting
                3. Directors Present and Absent
                4. Quorum Confirmation
                5. Appointment of Chairperson
                6. Clear Resolution Language ("IT WAS RESOLVED")
                7. Specific Resolutions with Details
                8. Voting Record (if applicable)
                9. Directors' Signatures
                10. Secretary Certification (if applicable)""",
                "type": "template",
                "document_type": "board_resolution"
            },
            {
                "id": "template_shareholder_resolution",
                "content": """Shareholder Resolution Template Requirements:
                1. Resolution of Incorporating Shareholders header
                2. Company Name (proposed)
                3. Date of Resolution
                4. List of Shareholders with shareholdings
                5. Appointment of Directors
                6. Appointment of Authorized Signatories
                7. Share Capital Structure
                8. Adoption of Articles
                9. Registered Office Address
                10. All Shareholders' Signatures with dates""",
                "type": "template",
                "document_type": "shareholder_resolution"
            }
        ]
        
        # Compliance rules and red flags
        compliance_rules = [
            {
                "id": "rule_jurisdiction",
                "content": """Jurisdiction Compliance Rules:
                - MUST reference "Abu Dhabi Global Market" or "ADGM"
                - MUST NOT reference "UAE Federal Courts", "Dubai Courts", "DIFC"
                - Governing law must be "ADGM Laws and Regulations"
                - Dispute resolution through "ADGM Courts"
                - Arbitration rules, if any, should reference "ADGM Arbitration Centre" """,
                "type": "compliance_rule",
                "category": "jurisdiction"
            },
            {
                "id": "rule_language",
                "content": """Legal Language Requirements:
                Binding Terms Required: shall, must, will, is required to, agrees to
                Weak Language to Avoid: may, might, could, possibly, perhaps, should consider
                Resolution Language: IT WAS RESOLVED, RESOLVED THAT, BE IT RESOLVED
                Obligation Language: undertakes, covenants, warrants, represents""",
                "type": "compliance_rule",
                "category": "language"
            },
            {
                "id": "rule_signatures",
                "content": """Signature Requirements:
                - All documents must have signature sections
                - Include full name fields for signatories
                - Date fields required for each signature
                - Witness requirements for certain documents
                - Electronic signatures acceptable with proper authentication""",
                "type": "compliance_rule",
                "category": "signatures"
            }
        ]
        
        # Add all documents to respective collections
        for reg in regulations:
            self._add_document(reg, "adgm_regulations")
        
        for template in templates:
            self._add_document(template, "document_templates")
        
        for rule in compliance_rules:
            self._add_document(rule, "compliance_rules")
        
        logger.info("Knowledge base loaded successfully")
    
    def _add_document(self, doc: Dict, collection_name: str):
        """Add document to ChromaDB collection with embedding"""
        try:
            embedding = self.embedder.encode(doc["content"]).tolist()
            
            metadata = {k: v for k, v in doc.items() if k not in ["id", "content"]}
            
            self.collections[collection_name].add(
                ids=[doc["id"]],
                documents=[doc["content"]],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            logger.info(f"Added document {doc['id']} to {collection_name}")
        except Exception as e:
            logger.error(f"Error adding document {doc['id']}: {e}")
    
    def hybrid_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Hybrid search combining dense and sparse retrieval
        """
        results = []
        
        # 1. Dense retrieval (semantic search)
        query_embedding = self.embedder.encode(query).tolist()
        
        for collection_name, collection in self.collections.items():
            try:
                dense_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k
                )
                
                if dense_results['documents'][0]:
                    for i, doc in enumerate(dense_results['documents'][0]):
                        results.append(Document(
                            id=dense_results['ids'][0][i],
                            content=doc,
                            metadata=dense_results['metadatas'][0][i],
                            score=1.0 - dense_results['distances'][0][i]
                        ))
            except Exception as e:
                logger.error(f"Error in dense retrieval from {collection_name}: {e}")
        
        # 2. Keyword search (BM25-like)
        keyword_results = self._keyword_search(query, k)
        results.extend(keyword_results)
        
        # 3. Remove duplicates and re-rank
        unique_results = self._deduplicate_results(results)
        reranked_results = self._rerank_results(query, unique_results)
        
        return reranked_results[:k]
    
    def _keyword_search(self, query: str, k: int = 5) -> List[Document]:
        """Simple keyword-based search"""
        results = []
        query_terms = set(query.lower().split())
        
        for collection_name, collection in self.collections.items():
            try:
                # Get all documents from collection
                all_docs = collection.get()
                
                if all_docs['documents']:
                    for i, doc in enumerate(all_docs['documents']):
                        doc_terms = set(doc.lower().split())
                        # Calculate Jaccard similarity
                        intersection = query_terms.intersection(doc_terms)
                        union = query_terms.union(doc_terms)
                        score = len(intersection) / len(union) if union else 0
                        
                        if score > 0:
                            results.append(Document(
                                id=all_docs['ids'][i],
                                content=doc,
                                metadata=all_docs['metadatas'][i] if all_docs['metadatas'] else {},
                                score=score
                            ))
            except Exception as e:
                logger.error(f"Error in keyword search from {collection_name}: {e}")
        
        return sorted(results, key=lambda x: x.score, reverse=True)[:k]
    
    def _deduplicate_results(self, results: List[Document]) -> List[Document]:
        """Remove duplicate documents based on ID"""
        seen = set()
        unique = []
        for doc in results:
            if doc.id not in seen:
                seen.add(doc.id)
                unique.append(doc)
        return unique
    
    def _rerank_results(self, query: str, documents: List[Document]) -> List[Document]:
        """Re-rank documents using cross-encoder"""
        if not documents:
            return documents
        
        # Prepare pairs for cross-encoder
        pairs = [[query, doc.content] for doc in documents]
        
        try:
            # Get cross-encoder scores
            scores = self.cross_encoder.predict(pairs)
            
            # Update document scores
            for doc, score in zip(documents, scores):
                doc.score = float(score)
            
            # Sort by score
            return sorted(documents, key=lambda x: x.score, reverse=True)
        except Exception as e:
            logger.error(f"Error in re-ranking: {e}")
            return documents
    
    def query_expansion(self, query: str) -> str:
        """Expand query with synonyms and related terms"""
        prompt = f"""Given this legal query about ADGM compliance, provide 3-5 related search terms or synonyms.
        Query: {query}
        
        Return only the expanded terms separated by commas, nothing else."""
        
        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt
            )
            
            expanded_terms = response['response'].strip()
            return f"{query} {expanded_terms}"
        except Exception as e:
            logger.error(f"Error in query expansion: {e}")
            return query
    
    def chain_of_thought_reasoning(self, query: str, context: str) -> Dict:
        """Multi-step reasoning for complex compliance questions"""
        
        prompt = f"""You are an ADGM legal compliance expert. Use chain-of-thought reasoning to analyze this compliance question.

Context from ADGM Regulations:
{context}

Question: {query}

Think through this step-by-step:
1. Identify the specific ADGM regulation or requirement being questioned
2. Check if the document/clause complies with identified regulations
3. List any specific violations or issues
4. Provide actionable recommendations

Respond in JSON format:
{{
    "reasoning_steps": ["step1", "step2", ...],
    "applicable_regulations": ["regulation1", "regulation2", ...],
    "compliance_status": "compliant/non-compliant/review_required",
    "issues": ["issue1", "issue2", ...],
    "recommendations": ["recommendation1", "recommendation2", ...],
    "confidence": 0.0-1.0
}}"""
        
        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                format="json"
            )
            
            result = json.loads(response['response'])
            return result
        except Exception as e:
            logger.error(f"Error in chain-of-thought reasoning: {e}")
            return {
                "reasoning_steps": ["Error in analysis"],
                "compliance_status": "review_required",
                "issues": ["Manual review needed"],
                "recommendations": ["Consult legal expert"],
                "confidence": 0.0
            }
    
    def validate_document(self, document_text: str, document_type: str) -> Dict:
        """
        Comprehensive document validation using Advanced RAG
        """
        # Expand query for better retrieval
        base_query = f"ADGM requirements for {document_type}"
        expanded_query = self.query_expansion(base_query)
        
        # Perform hybrid search
        relevant_docs = self.hybrid_search(expanded_query, k=10)
        
        # Build context from retrieved documents
        context = "\n\n".join([doc.content for doc in relevant_docs[:5]])
        
        # Perform chain-of-thought analysis
        analysis = self.chain_of_thought_reasoning(
            f"Validate this {document_type}: {document_text[:1000]}",
            context
        )
        
        return {
            "document_type": document_type,
            "compliance_status": analysis.get("compliance_status", "review_required"),
            "issues": analysis.get("issues", []),
            "recommendations": analysis.get("recommendations", []),
            "applicable_regulations": analysis.get("applicable_regulations", []),
            "confidence": analysis.get("confidence", 0.0),
            "sources": [doc.metadata.get("source", "Unknown") for doc in relevant_docs[:3]]
        }
    
    def suggest_corrections(self, text: str, issues: List[str]) -> str:
        """Generate corrected text based on identified issues"""
        
        issues_text = "\n".join([f"- {issue}" for issue in issues])
        
        prompt = f"""You are an ADGM legal expert. Correct the following text to comply with ADGM regulations.

Original Text:
{text}

Issues Found:
{issues_text}

Provide the corrected text that:
1. Complies with all ADGM regulations
2. Uses proper legal language (binding terms)
3. References ADGM jurisdiction correctly
4. Includes all required elements

Return only the corrected text:"""
        
        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt
            )
            
            return response['response'].strip()
        except Exception as e:
            logger.error(f"Error generating corrections: {e}")
            return text