#!/usr/bin/env python3
"""
ADGM Corporate Agent - Complete Implementation
A comprehensive RAG-powered document review system for ADGM compliance
"""

# ===== 1. document_processor.py =====
"""
Document Processor Module
Handles document loading, parsing, and manipulation
"""

from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_COLOR_INDEX
import re
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process and analyze ADGM legal documents"""
    
    def __init__(self):
        self.document = None
        self.document_type = None
        self.document_path = None
        self.issues = []
        
    def load_document(self, file_path: str) -> bool:
        """Load a Word document for processing"""
        try:
            self.document = Document(file_path)
            self.document_path = file_path
            self.document_type = self._identify_document_type()
            logger.info(f"Loaded document: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            return False
    
    def _identify_document_type(self) -> str:
        """Identify the type of legal document based on content"""
        if not self.document:
            return "unknown"
        
        text = self.get_document_text().lower()
        
        # Document type patterns
        patterns = {
            "articles_of_association": ["articles of association", "aoa", "article 1", "share capital", "registered office"],
            "board_resolution": ["board resolution", "board of directors", "it was resolved", "directors present"],
            "shareholder_resolution": ["shareholder resolution", "shareholders", "resolved", "incorporating"],
            "memorandum": ["memorandum of association", "moa", "objects of the company"],
            "employment_contract": ["employment agreement", "employee", "salary", "duties", "termination"],
            "commercial_agreement": ["agreement", "services", "payment", "parties", "terms"],
            "ubo_declaration": ["ultimate beneficial owner", "ubo", "beneficial ownership"],
            "incorporation_form": ["incorporation", "application", "company formation"],
            "register": ["register of members", "register of directors", "shareholding"]
        }
        
        for doc_type, keywords in patterns.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches >= 2:
                return doc_type
        
        return "general_document"
    
    def get_document_text(self) -> str:
        """Extract all text from the document"""
        if not self.document:
            return ""
        
        full_text = []
        for paragraph in self.document.paragraphs:
            full_text.append(paragraph.text)
        
        # Also extract text from tables
        for table in self.document.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text.append(cell.text)
        
        return "\n".join(full_text)
    
    def check_jurisdiction(self) -> List[Dict]:
        """Check for correct ADGM jurisdiction references"""
        issues = []
        text = self.get_document_text()
        
        # Red flag jurisdictions
        incorrect_jurisdictions = [
            "UAE Federal Courts",
            "Dubai Courts", 
            "Abu Dhabi Courts",
            "Sharjah Courts",
            "DIFC",
            "Dubai International Financial Centre",
            "mainland UAE",
            "onshore UAE"
        ]
        
        for jurisdiction in incorrect_jurisdictions:
            if jurisdiction.lower() in text.lower():
                issues.append({
                    "issue": f"Incorrect jurisdiction reference: '{jurisdiction}'",
                    "severity": "high",
                    "suggestion": "Replace with 'Abu Dhabi Global Market (ADGM)' or 'ADGM Courts'",
                    "regulation": "ADGM Companies Regulations 2020, Art. 6"
                })
        
        # Check for correct ADGM references
        adgm_patterns = ["abu dhabi global market", "adgm", "adgm courts", "adgm jurisdiction"]
        has_adgm = any(pattern in text.lower() for pattern in adgm_patterns)
        
        if not has_adgm and self.document_type in ["articles_of_association", "board_resolution", "shareholder_resolution"]:
            issues.append({
                "issue": "Missing ADGM jurisdiction reference",
                "severity": "high",
                "suggestion": "Add explicit reference to 'Abu Dhabi Global Market (ADGM)' jurisdiction",
                "regulation": "ADGM Companies Regulations 2020, Art. 6"
            })
        
        return issues
    
    def check_weak_language(self) -> List[Dict]:
        """Check for weak or non-binding language"""
        issues = []
        text = self.get_document_text()
        
        weak_terms = [
            ("may", "shall"),
            ("might", "shall"),
            ("could", "shall"),
            ("possibly", "shall"),
            ("perhaps", "shall"),
            ("should consider", "shall"),
            ("maybe", "shall"),
            ("potentially", "shall"),
            ("presumably", "shall"),
            ("arguably", "shall")
        ]
        
        for weak, strong in weak_terms:
            pattern = r'\b' + weak + r'\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get context around the match
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]
                
                issues.append({
                    "issue": f"Weak language detected: '{weak}'",
                    "severity": "medium",
                    "suggestion": f"Replace '{weak}' with '{strong}' for binding effect",
                    "context": context.strip(),
                    "regulation": "ADGM legal drafting standards"
                })
        
        return issues
    
    def check_required_sections(self) -> List[Dict]:
        """Check for required sections based on document type"""
        issues = []
        text = self.get_document_text().lower()
        
        required_sections = {
            "articles_of_association": [
                "company name",
                "registered office", 
                "share capital",
                "directors",
                "shareholders",
                "meetings",
                "governing law"
            ],
            "board_resolution": [
                "date",
                "directors present",
                "quorum",
                "resolved",
                "signatures"
            ],
            "shareholder_resolution": [
                "shareholders",
                "shareholdings",
                "resolved",
                "signatures"
            ],
            "employment_contract": [
                "parties",
                "position",
                "duties",
                "compensation",
                "term",
                "termination"
            ]
        }
        
        if self.document_type in required_sections:
            for section in required_sections[self.document_type]:
                if section not in text:
                    issues.append({
                        "issue": f"Missing required section: '{section}'",
                        "severity": "high",
                        "suggestion": f"Add a section covering '{section}'",
                        "regulation": f"ADGM {self.document_type.replace('_', ' ').title()} requirements"
                    })
        
        return issues
    
    def check_signatory_sections(self) -> List[Dict]:
        """Check for proper signatory sections"""
        issues = []
        text = self.get_document_text().lower()
        
        # Check for signature blocks
        signature_indicators = ["signature", "signed", "authorized signatory", "name:", "date:", "_______"]
        has_signature_section = any(indicator in text for indicator in signature_indicators)
        
        if not has_signature_section:
            issues.append({
                "issue": "Missing signature section",
                "severity": "high",
                "suggestion": "Add proper signature blocks with name, title, and date fields",
                "regulation": "ADGM execution requirements"
            })
        
        # Check for date fields
        if "date" not in text and "dated" not in text:
            issues.append({
                "issue": "Missing date field",
                "severity": "medium",
                "suggestion": "Add date field for execution",
                "regulation": "ADGM documentation standards"
            })
        
        return issues
    
    def insert_comment(self, paragraph_index: int, comment_text: str):
        """Insert a comment at a specific paragraph"""
        if not self.document or paragraph_index >= len(self.document.paragraphs):
            return
        
        para = self.document.paragraphs[paragraph_index]
        # Add comment as highlighted text (Word doesn't support true comments via python-docx)
        run = para.add_run(f" [COMMENT: {comment_text}]")
        run.font.color.rgb = RGBColor(255, 0, 0)
        run.font.italic = True
    
    def highlight_text(self, search_text: str, comment: str):
        """Highlight specific text and add comment"""
        for i, paragraph in enumerate(self.document.paragraphs):
            if search_text.lower() in paragraph.text.lower():
                # Create new paragraph with highlighting
                for run in paragraph.runs:
                    if search_text.lower() in run.text.lower():
                        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                
                # Add comment
                self.insert_comment(i, comment)
    
    def save_reviewed_document(self, output_path: str):
        """Save the reviewed document with comments and highlights"""
        if not self.document:
            return False
        
        try:
            # Add header with review summary
            first_para = self.document.paragraphs[0].insert_paragraph_before(
                "===== ADGM COMPLIANCE REVIEW =====\n"
            )
            first_para.runs[0].font.bold = True
            first_para.runs[0].font.color.rgb = RGBColor(0, 0, 255)
            
            # Add review metadata
            meta_para = first_para.insert_paragraph_before(
                f"Document Type: {self.document_type.replace('_', ' ').title()}\n"
                f"Review Status: Completed\n"
                f"Issues Found: {len(self.issues)}\n"
                "=" * 50 + "\n"
            )
            
            self.document.save(output_path)
            logger.info(f"Saved reviewed document to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False