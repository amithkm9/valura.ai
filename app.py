"""
ADGM Corporate Agent - Streamlit Application (Enhanced)
Fixed document processing and reporting
"""

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import tempfile
import logging
from typing import List, Dict, Tuple
import zipfile
import time

from document_processor import DocumentProcessor
from compliance_checker import ComplianceChecker
from advanced_rag import AdvancedRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ADGM Corporate Agent",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 2rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        text-align: center;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.25rem;
    }
    
    .status-pass {
        background: #10b981;
        color: white;
    }
    
    .status-fail {
        background: #ef4444;
        color: white;
    }
    
    .status-warning {
        background: #f59e0b;
        color: white;
    }
    
    .status-info {
        background: #3b82f6;
        color: white;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* File uploader styling */
    .uploadedFile {
        background: #f3f4f6;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
    }
    
    /* Alert boxes */
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-success {
        background: #d1fae5;
        border-left: 4px solid #10b981;
    }
    
    .alert-warning {
        background: #fed7aa;
        border-left: 4px solid #f59e0b;
    }
    
    .alert-error {
        background: #fee2e2;
        border-left: 4px solid #ef4444;
    }
    
    .alert-info {
        background: #dbeafe;
        border-left: 4px solid #3b82f6;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: transparent;
        border-radius: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class ADGMCorporateAgent:
    """Enhanced main application class for ADGM document review"""
    
    def __init__(self):
        logger.info("Initializing ADGM Corporate Agent...")
        
        self.processors = {}  # Store multiple processors for multiple documents
        self.checker = ComplianceChecker()
        self.rag = AdvancedRAG(model_name="llama2")
        
        # Create output directory
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Session storage
        self.session_results = []
        self.document_types = []  # Track document types
        
        logger.info("ADGM Corporate Agent initialized successfully")
    
    def process_single_document(self, file_path: str, file_name: str) -> Dict:
        """Enhanced document processing with proper type identification"""
        
        logger.info(f"Processing document: {file_name}")
        
        try:
            # Create new processor for this document
            processor = DocumentProcessor()
            
            # Load and identify document
            if not processor.load_document(file_path):
                raise Exception("Failed to load document")
            
            doc_type = processor.document_type
            self.document_types.append(doc_type)  # Track document type
            logger.info(f"Document type identified: {doc_type}")
            
            # Extract document text
            doc_text = processor.get_document_text()
            
            # Perform comprehensive review with inline comments
            issues = processor.perform_comprehensive_review()
            
            # Perform Advanced RAG validation
            rag_validation = self.rag.validate_document(doc_text, doc_type)
            
            # Add RAG-identified issues
            for i, rag_issue in enumerate(rag_validation.get("issues", [])):
                issues.append({
                    "issue": rag_issue,
                    "severity": "medium" if rag_validation["confidence"] < 0.7 else "high",
                    "suggestion": rag_validation["recommendations"][i] if i < len(rag_validation["recommendations"]) else "Review with legal counsel",
                    "regulation": ", ".join(rag_validation.get("applicable_regulations", ["ADGM Compliance"])),
                    "source": "AI Analysis (Advanced RAG)"
                })
            
            # Generate AI suggestions for high-severity issues
            high_issues = [issue for issue in issues if issue["severity"] == "high"]
            if high_issues and len(doc_text) > 100:
                sample_text = doc_text[:500]
                issue_descriptions = [issue["issue"] for issue in high_issues[:3]]
                corrected_text = self.rag.suggest_corrections(sample_text, issue_descriptions)
                
                if corrected_text != sample_text:
                    issues.append({
                        "issue": "AI-generated corrections available",
                        "severity": "info",
                        "suggestion": "Review suggested corrections below",
                        "corrected_sample": corrected_text[:300] + "...",
                        "source": "AI Suggestion"
                    })
            
            # Save reviewed document with comments
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{Path(file_name).stem}_reviewed_{timestamp}.docx"
            output_path = self.output_dir / output_filename
            
            # Save the document
            if processor.save_reviewed_document(str(output_path)):
                logger.info(f"Saved reviewed document: {output_path}")
            else:
                logger.warning(f"Failed to save reviewed document: {output_path}")
                output_path = None
            
            # Store processor for potential reuse
            self.processors[file_name] = processor
            
            result = {
                "file_name": file_name,
                "document_type": doc_type,
                "issues_found": len(issues),
                "issues": issues,
                "reviewed_file": str(output_path) if output_path else None,
                "comments_added": len(processor.comments_added),
                "rag_validation": {
                    "compliance_status": rag_validation.get("compliance_status", "unknown"),
                    "confidence": rag_validation.get("confidence", 0.0),
                    "sources": rag_validation.get("sources", [])
                }
            }
            
            logger.info(f"Document processed successfully: {file_name} with {len(issues)} issues")
            return result
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}", exc_info=True)
            return {
                "file_name": file_name,
                "document_type": "error",
                "issues_found": 0,
                "issues": [{
                    "issue": f"Error processing file: {str(e)}",
                    "severity": "critical",
                    "source": "System"
                }],
                "reviewed_file": None,
                "comments_added": 0
            }
    
    def process_documents(self, files) -> Tuple[List[Dict], Dict, List[str]]:
        """Process multiple uploaded documents with enhanced tracking"""
        
        if not files:
            return [], {}, []
        
        logger.info(f"Processing {len(files)} documents...")
        
        results = []
        doc_names = []
        all_reviewed_files = []
        self.document_types = []  # Reset document types
        
        # Process each document
        for file in files:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_path = tmp_file.name
            
            file_name = file.name
            doc_names.append(file_name)
            
            result = self.process_single_document(tmp_path, file_name)
            results.append(result)
            
            if result.get("reviewed_file"):
                all_reviewed_files.append(result["reviewed_file"])
            
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        # Store results in session
        self.session_results = results
        
        # Check for missing documents using document types
        process_type = self.checker.identify_process_type(self.document_types)
        doc_check = self.checker.check_missing_documents(
            doc_names, 
            process_type,
            self.document_types  # Pass document types for better matching
        )
        
        # Compile all issues
        all_issues = []
        for result in results:
            for issue in result["issues"]:
                all_issues.append({
                    "document": result["file_name"],
                    "type": result["document_type"],
                    **issue
                })
        
        # Generate comprehensive compliance report
        report = self._generate_comprehensive_report(results, doc_check, all_issues)
        
        return results, report, all_reviewed_files
    
    def _generate_comprehensive_report(self, results: List[Dict], doc_check: Dict, all_issues: List[Dict]) -> Dict:
        """Generate enhanced comprehensive compliance report"""
        
        # Count issues by severity
        severity_count = {
            "critical": sum(1 for issue in all_issues if issue.get("severity") == "critical"),
            "high": sum(1 for issue in all_issues if issue.get("severity") == "high"),
            "medium": sum(1 for issue in all_issues if issue.get("severity") == "medium"),
            "low": sum(1 for issue in all_issues if issue.get("severity") == "low"),
            "info": sum(1 for issue in all_issues if issue.get("severity") == "info")
        }
        
        # Count issues by source
        source_count = {
            "Rule-based Check": sum(1 for issue in all_issues if "Rule-based" in issue.get("source", "")),
            "AI Analysis": sum(1 for issue in all_issues if "AI" in issue.get("source", "")),
            "AI Suggestion": sum(1 for issue in all_issues if "Suggestion" in issue.get("source", "")),
            "System": sum(1 for issue in all_issues if issue.get("source") == "System")
        }
        
        # Calculate compliance score
        score, status = self.checker.calculate_compliance_score(all_issues, doc_check)
        
        # Collect all RAG validation results
        rag_validations = []
        for result in results:
            if "rag_validation" in result:
                rag_validations.append({
                    "document": result["file_name"],
                    "document_type": result["document_type"],
                    **result["rag_validation"]
                })
        
        # Generate recommendations
        recommendations = self.checker.generate_recommendations(all_issues, doc_check)
        
        # Count total comments added
        total_comments = sum(result.get("comments_added", 0) for result in results)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "process_type": doc_check.get("process", "unknown"),
            "documents_uploaded": doc_check.get("uploaded_count", 0),
            "documents_present": doc_check.get("present_documents", []),
            "required_documents": doc_check.get("required_count", 0),
            "missing_documents": doc_check.get("missing_documents", []),
            "total_issues": len(all_issues),
            "total_comments_added": total_comments,
            "severity_breakdown": severity_count,
            "issue_source_breakdown": source_count,
            "issues_detail": all_issues,
            "compliance_score": score,
            "compliance_status": status,
            "ai_validations": rag_validations,
            "recommendations": recommendations,
            "review_method": "Hybrid (Rule-based + Advanced RAG with Inline Comments)",
            "document_types_identified": self.document_types
        }
    
    def export_all_results(self) -> str:
        """Export all reviewed documents and report as a zip file"""
        if not self.session_results:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.output_dir / f"adgm_review_package_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add reviewed documents
            for result in self.session_results:
                if result.get("reviewed_file") and os.path.exists(result["reviewed_file"]):
                    zipf.write(result["reviewed_file"], os.path.basename(result["reviewed_file"]))
            
            # Add JSON report
            if hasattr(self, 'last_report'):
                report_path = self.output_dir / f"compliance_report_{timestamp}.json"
                with open(report_path, 'w') as f:
                    json.dump(self.last_report, f, indent=2)
                zipf.write(report_path, os.path.basename(report_path))
        
        return str(zip_path) if zip_path.exists() else None

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = ADGMCorporateAgent()
    st.session_state.processed = False
    st.session_state.results = []
    st.session_state.report = {}
    st.session_state.reviewed_files = []

def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🏛️ ADGM Corporate Agent</div>
        <div class="header-subtitle">Advanced RAG-Powered Legal Document Review System</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # File Upload Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📤 Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Select ADGM Documents",
            type=['docx'],
            accept_multiple_files=True,
            help="Upload one or more Word documents (.docx) for compliance review"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} document(s) uploaded")
            for file in uploaded_files:
                st.markdown(f"📄 {file.name}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            process_button = st.button(
                "🔍 Review Documents",
                type="primary",
                use_container_width=True,
                disabled=not uploaded_files
            )
        
        with col_btn2:
            export_button = st.button(
                "📦 Export All",
                use_container_width=True,
                disabled=not st.session_state.processed
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # System Status
        with st.expander("⚙️ System Status", expanded=False):
            status_cols = st.columns(2)
            with status_cols[0]:
                st.markdown("""
                🟢 **Ollama Model:** llama2  
                🟢 **Vector DB:** ChromaDB  
                🟢 **Embeddings:** MiniLM-L6
                """)
            with status_cols[1]:
                st.markdown("""
                ✅ Hybrid Search  
                ✅ Query Expansion  
                ✅ Chain-of-Thought
                """)
        
        # Supported Documents
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📑 Supported Documents")
        
        doc_types = {
            "Company Formation": [
                "Articles of Association",
                "Board/Shareholder Resolutions",
                "Incorporation Forms",
                "Register of Members/Directors"
            ],
            "Licensing": [
                "License Applications",
                "Business Plans",
                "Compliance Manuals"
            ],
            "Employment": [
                "Employment Contracts",
                "Job Descriptions",
                "Salary Certificates"
            ]
        }
        
        for category, docs in doc_types.items():
            with st.expander(category):
                for doc in docs:
                    st.markdown(f"• {doc}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Results Section
        if process_button and uploaded_files:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 🔄 Processing Documents...")
            
            # Process documents with progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, file in enumerate(uploaded_files):
                status_text.text(f"Processing: {file.name}")
                progress_bar.progress((i + 1) / len(uploaded_files))
                time.sleep(0.5)  # Simulate processing time
            
            # Process documents
            results, report, reviewed_files = st.session_state.agent.process_documents(uploaded_files)
            st.session_state.processed = True
            st.session_state.results = results
            st.session_state.report = report
            st.session_state.reviewed_files = reviewed_files
            
            progress_bar.empty()
            status_text.empty()
            st.markdown('</div>', unsafe_allow_html=True)
            st.rerun()
        
        if st.session_state.processed:
            # Display metrics
            st.markdown("### 📊 Compliance Overview")
            
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{st.session_state.report["documents_uploaded"]}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Documents</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with metric_cols[1]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{st.session_state.report["total_issues"]}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Total Issues</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with metric_cols[2]:
                high_issues = st.session_state.report["severity_breakdown"]["high"]
                color = "🔴" if high_issues > 0 else "🟢"
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{color} {high_issues}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">High Severity</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with metric_cols[3]:
                status = st.session_state.report["compliance_status"]
                if "PASS" in status:
                    badge_class = "status-pass"
                    icon = "✅"
                elif "CRITICAL" in status:
                    badge_class = "status-fail"
                    icon = "🚫"
                elif "FAIL" in status:
                    badge_class = "status-fail"
                    icon = "❌"
                else:
                    badge_class = "status-warning"
                    icon = "⚠️"
                
                st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{icon}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-label">Status</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Tabs for detailed results
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🔍 Issues", "📊 AI Analysis", "📥 Downloads"])
            
            with tab1:
                # Compliance Status
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### Compliance Status")
                
                if "PASS" in status:
                    st.success(f"✅ {status}")
                elif "CRITICAL" in status or "FAIL" in status:
                    st.error(f"❌ {status}")
                else:
                    st.warning(f"⚠️ {status}")
                
                # Missing Documents
                if st.session_state.report["missing_documents"]:
                    st.markdown("#### Missing Documents")
                    for doc in st.session_state.report["missing_documents"]:
                        st.markdown(f'<div class="alert-box alert-warning">📄 {doc}</div>', unsafe_allow_html=True)
                
                # Recommendations
                st.markdown("#### 💡 Recommendations")
                for rec in st.session_state.report["recommendations"]:
                    st.info(rec)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab2:
                # Issues Detail
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### Issues by Severity")
                
                # Group issues by severity
                for severity in ["critical", "high", "medium", "low", "info"]:
                    severity_issues = [
                        issue for issue in st.session_state.report["issues_detail"]
                        if issue.get("severity") == severity
                    ]
                    
                    if severity_issues:
                        severity_emoji = {
                            "critical": "🚫",
                            "high": "🔴",
                            "medium": "🟡",
                            "low": "🟢",
                            "info": "ℹ️"
                        }[severity]
                        
                        with st.expander(f"{severity_emoji} {severity.upper()} ({len(severity_issues)} issues)"):
                            for issue in severity_issues:
                                st.markdown(f"**Document:** {issue['document']}")
                                st.markdown(f"**Issue:** {issue['issue']}")
                                st.markdown(f"**Suggestion:** {issue.get('suggestion', 'N/A')}")
                                st.markdown(f"**Source:** {issue.get('source', 'Unknown')}")
                                st.markdown("---")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab3:
                # AI Analysis
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### AI Validation Results")
                
                if st.session_state.report.get("ai_validations"):
                    for validation in st.session_state.report["ai_validations"]:
                        confidence = validation["confidence"]
                        confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                        
                        st.markdown(f"**Document:** {validation['document']}")
                        st.markdown(f"**Status:** {validation['compliance_status']}")
                        st.markdown(f"**Confidence:** {confidence_color} {confidence:.1%}")
                        
                        if validation.get("sources"):
                            st.markdown(f"**Sources:** {', '.join(validation['sources'])}")
                        st.markdown("---")
                
                # Analysis Method Breakdown
                st.markdown("#### Analysis Methods")
                col_method1, col_method2 = st.columns(2)
                
                with col_method1:
                    st.metric(
                        "Rule-based Checks",
                        st.session_state.report["issue_source_breakdown"].get("Rule-based Check", 0)
                    )
                
                with col_method2:
                    st.metric(
                        "AI Analysis (RAG)",
                        st.session_state.report["issue_source_breakdown"].get("AI Analysis", 0)
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab4:
                # Downloads
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### Download Reviewed Documents")
                
                if st.session_state.reviewed_files:
                    for file_path in st.session_state.reviewed_files:
                        if os.path.exists(file_path):
                            file_name = os.path.basename(file_path)
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                    label=f"📥 Download {file_name}",
                                    data=f.read(),
                                    file_name=file_name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                
                # Export all as ZIP
                if export_button:
                    zip_path = st.session_state.agent.export_all_results()
                    if zip_path and os.path.exists(zip_path):
                        with open(zip_path, 'rb') as f:
                            st.download_button(
                                label="📦 Download All (ZIP)",
                                data=f.read(),
                                file_name=os.path.basename(zip_path),
                                mime="application/zip"
                            )
                
                # Export JSON Report
                st.markdown("#### Export Report")
                report_json = json.dumps(st.session_state.report, indent=2)
                st.download_button(
                    label="📊 Download JSON Report",
                    data=report_json,
                    file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 2rem;">
        <p><strong>🔒 Privacy & Security</strong></p>
        <p>All processing happens locally - no data leaves your system</p>
        <p style="margin-top: 1rem;">
            <em>⚠️ Disclaimer: This system provides automated compliance checking based on ADGM regulations.
            For final submission, always consult with qualified legal counsel.</em>
        </p>
        <p style="margin-top: 2rem; font-size: 0.9rem;">
            Powered by Ollama, ChromaDB, and Advanced RAG Technology
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # Configure page settings
    print("=" * 60)
    print("ADGM Corporate Agent - Advanced RAG System")
    print("=" * 60)
    print("\n✅ Initializing system components...")
    print("📦 Loading knowledge base...")
    print("🤖 Connecting to Ollama...")
    print("\nMake sure Ollama is running: ollama serve")
    print("=" * 60)
    print("\n🚀 Launching Streamlit application...")
    print("📍 Access at: http://localhost:8501")
    print("=" * 60)
    
    # Run the main application
    main()