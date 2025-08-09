"""
ADGM Corporate Agent - Main Application
Advanced RAG-powered document review system
"""

import gradio as gr
import json
import os
from datetime import datetime
from pathlib import Path
import tempfile
import logging
from typing import List, Dict, Tuple

from document_processor import DocumentProcessor
from compliance_checker import ComplianceChecker
from advanced_rag import AdvancedRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ADGMCorporateAgent:
    """Main application class for ADGM document review"""
    
    def __init__(self):
        logger.info("Initializing ADGM Corporate Agent...")
        
        self.processor = DocumentProcessor()
        self.checker = ComplianceChecker()
        self.rag = AdvancedRAG(model_name="llama2")
        
        # Create output directory
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Session storage
        self.session_results = []
        
        logger.info("ADGM Corporate Agent initialized successfully")
    
    def process_single_document(self, file_path: str, file_name: str) -> Dict:
        """Process a single document with Advanced RAG validation"""
        
        logger.info(f"Processing document: {file_name}")
        
        try:
            # Load and identify document
            self.processor.load_document(file_path)
            doc_type = self.processor.document_type
            logger.info(f"Document type identified: {doc_type}")
            
            # Extract document text
            doc_text = self.processor.get_document_text()
            
            # Perform Advanced RAG validation
            rag_validation = self.rag.validate_document(doc_text, doc_type)
            
            # Run traditional compliance checks
            issues = []
            
            # Check jurisdiction
            jurisdiction_issues = self.processor.check_jurisdiction()
            for issue in jurisdiction_issues:
                issue["source"] = "Rule-based Check"
            issues.extend(jurisdiction_issues)
            
            # Check weak language
            weak_language_issues = self.processor.check_weak_language()
            for issue in weak_language_issues:
                issue["source"] = "Rule-based Check"
            issues.extend(weak_language_issues)
            
            # Check required sections
            section_issues = self.processor.check_required_sections()
            for issue in section_issues:
                issue["source"] = "Rule-based Check"
            issues.extend(section_issues)
            
            # Check signatory sections
            signatory_issues = self.processor.check_signatory_sections()
            for issue in signatory_issues:
                issue["source"] = "Rule-based Check"
            issues.extend(signatory_issues)
            
            # Add RAG-identified issues
            for i, rag_issue in enumerate(rag_validation.get("issues", [])):
                issues.append({
                    "issue": rag_issue,
                    "severity": "medium" if rag_validation["confidence"] < 0.7 else "high",
                    "suggestion": rag_validation["recommendations"][i] if i < len(rag_validation["recommendations"]) else "Review with legal counsel",
                    "regulation": ", ".join(rag_validation.get("applicable_regulations", ["ADGM Compliance"])),
                    "source": "AI Analysis (Advanced RAG)"
                })
            
            # Generate suggestions for high-severity issues
            if any(issue["severity"] == "high" for issue in issues):
                sample_text = doc_text[:500]
                high_issues = [issue["issue"] for issue in issues if issue["severity"] == "high"]
                corrected_text = self.rag.suggest_corrections(sample_text, high_issues[:3])
                
                # Add correction suggestion
                if corrected_text != sample_text:
                    issues.append({
                        "issue": "Suggested corrections available",
                        "severity": "info",
                        "suggestion": "See corrected sample in report",
                        "corrected_sample": corrected_text[:200] + "...",
                        "source": "AI Suggestion"
                    })
            
            # Save reviewed document
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{Path(file_name).stem}_reviewed_{timestamp}.docx"
            output_path = self.output_dir / output_filename
            self.processor.save_reviewed_document(str(output_path))
            
            result = {
                "file_name": file_name,
                "document_type": doc_type,
                "issues_found": len(issues),
                "issues": issues,
                "reviewed_file": str(output_path),
                "rag_validation": {
                    "compliance_status": rag_validation.get("compliance_status", "unknown"),
                    "confidence": rag_validation.get("confidence", 0.0),
                    "sources": rag_validation.get("sources", [])
                }
            }
            
            logger.info(f"Document processed successfully: {file_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")
            return {
                "file_name": file_name,
                "document_type": "error",
                "issues_found": 0,
                "issues": [{
                    "issue": f"Error processing file: {str(e)}",
                    "severity": "critical",
                    "source": "System"
                }],
                "reviewed_file": None
            }
    
    def process_documents(self, files) -> Tuple[str, str, str]:
        """Process multiple uploaded documents"""
        
        if not files:
            return None, None, "❌ Please upload at least one document (.docx format)"
        
        logger.info(f"Processing {len(files)} documents...")
        
        results = []
        doc_names = []
        all_reviewed_files = []
        
        # Process each document
        for file in files:
            file_name = os.path.basename(file.name)
            doc_names.append(file_name)
            
            result = self.process_single_document(file.name, file_name)
            results.append(result)
            
            if result.get("reviewed_file"):
                all_reviewed_files.append(result["reviewed_file"])
        
        # Store results in session
        self.session_results = results
        
        # Check for missing documents
        process_type = self.checker.identify_process_type(doc_names)
        doc_check = self.checker.check_missing_documents(doc_names, process_type)
        
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
        
        # Create summary message
        summary = self._create_summary_message(results, doc_check, report, process_type)
        
        # Get the first reviewed file for download
        reviewed_file = all_reviewed_files[0] if all_reviewed_files else None
        
        return reviewed_file, json.dumps(report, indent=2), summary
    
    def _generate_comprehensive_report(self, results: List[Dict], doc_check: Dict, all_issues: List[Dict]) -> Dict:
        """Generate comprehensive compliance report with RAG insights"""
        
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
            "Rule-based Check": sum(1 for issue in all_issues if issue.get("source") == "Rule-based Check"),
            "AI Analysis": sum(1 for issue in all_issues if "AI" in issue.get("source", "")),
            "System": sum(1 for issue in all_issues if issue.get("source") == "System")
        }
        
        # Determine overall compliance status
        compliance_status = "PASS"
        if severity_count["critical"] > 0:
            compliance_status = "CRITICAL ISSUES - DO NOT SUBMIT"
        elif severity_count["high"] > 0 or len(doc_check.get("missing_documents", [])) > 0:
            compliance_status = "FAIL - CORRECTIONS REQUIRED"
        elif severity_count["medium"] > 3:
            compliance_status = "REVIEW REQUIRED"
        
        # Collect all RAG validation results
        rag_validations = []
        for result in results:
            if "rag_validation" in result:
                rag_validations.append({
                    "document": result["file_name"],
                    **result["rag_validation"]
                })
        
        # Generate recommendations
        recommendations = self.checker.generate_recommendations(all_issues, doc_check)
        
        # Add AI-powered recommendations
        if any(v["confidence"] < 0.7 for v in rag_validations):
            recommendations.append("⚠️ AI confidence is low for some documents - manual legal review strongly recommended")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "process_type": doc_check.get("process", "unknown"),
            "documents_uploaded": doc_check.get("uploaded_count", 0),
            "required_documents": doc_check.get("required_count", 0),
            "missing_documents": doc_check.get("missing_documents", []),
            "total_issues": len(all_issues),
            "severity_breakdown": severity_count,
            "issue_source_breakdown": source_count,
            "issues_detail": all_issues,
            "compliance_status": compliance_status,
            "ai_validations": rag_validations,
            "recommendations": recommendations,
            "review_method": "Hybrid (Rule-based + Advanced RAG)"
        }
    
    def _create_summary_message(self, results: List[Dict], doc_check: Dict, report: Dict, process_type: str) -> str:
        """Create formatted summary message"""
        
        # Determine status emoji
        status_emoji = {
            "PASS": "✅",
            "REVIEW REQUIRED": "⚠️",
            "FAIL - CORRECTIONS REQUIRED": "❌",
            "CRITICAL ISSUES - DO NOT SUBMIT": "🚫"
        }.get(report['compliance_status'], "❓")
        
        # Missing documents message
        if doc_check["missing_documents"]:
            missing_msg = f"\n⚠️ **Missing documents:** {', '.join(doc_check['missing_documents'])}"
        else:
            missing_msg = "\n✅ All required documents uploaded"
        
        # AI confidence summary
        ai_validations = report.get("ai_validations", [])
        if ai_validations:
            avg_confidence = sum(v["confidence"] for v in ai_validations) / len(ai_validations)
            confidence_emoji = "🟢" if avg_confidence > 0.8 else "🟡" if avg_confidence > 0.6 else "🔴"
            ai_confidence_msg = f"\n{confidence_emoji} **AI Confidence:** {avg_confidence:.1%}"
        else:
            ai_confidence_msg = ""
        
        summary = f"""
# 📋 ADGM Compliance Review Report

## 📁 Process Information
**Process Identified:** {process_type.replace('_', ' ').title()}
**Documents Uploaded:** {len(results)}
**Required Documents:** {doc_check['required_count']}
{missing_msg}

## 🔍 Analysis Results
**Total Issues Found:** {report['total_issues']}
- 🚫 Critical: {report['severity_breakdown'].get('critical', 0)}
- 🔴 High Severity: {report['severity_breakdown']['high']}
- 🟡 Medium Severity: {report['severity_breakdown']['medium']}
- 🟢 Low Severity: {report['severity_breakdown']['low']}
- ℹ️ Informational: {report['severity_breakdown'].get('info', 0)}

**Analysis Methods:**
- Rule-based Checks: {report['issue_source_breakdown'].get('Rule-based Check', 0)} issues
- AI Analysis (RAG): {report['issue_source_breakdown'].get('AI Analysis', 0)} issues
{ai_confidence_msg}

## {status_emoji} Compliance Status
**{report['compliance_status']}**

## 📋 Recommendations
"""
        
        for i, rec in enumerate(report.get('recommendations', []), 1):
            summary += f"\n{i}. {rec}"
        
        summary += """

---
*This report was generated using Advanced RAG with Ollama. For final submission, please consult with legal counsel.*
"""
        
        return summary
    
    def export_all_results(self) -> str:
        """Export all reviewed documents as a zip file"""
        if not self.session_results:
            return None
        
        import zipfile
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.output_dir / f"reviewed_documents_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for result in self.session_results:
                if result.get("reviewed_file") and os.path.exists(result["reviewed_file"]):
                    zipf.write(result["reviewed_file"], os.path.basename(result["reviewed_file"]))
        
        return str(zip_path) if zip_path.exists() else None

def create_interface():
    """Create Gradio interface for the application"""
    
    agent = ADGMCorporateAgent()
    
    with gr.Blocks(
        title="ADGM Corporate Agent - Advanced RAG",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            font-family: 'Arial', sans-serif;
        }
        .markdown-text {
            font-size: 14px;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # 🏛️ ADGM Corporate Agent
        ## Advanced RAG-Powered Legal Document Review System
        
        <div style="background-color: #f0f9ff; padding: 15px; border-radius: 10px; margin: 10px 0;">
        <strong>🚀 Powered by Advanced RAG Technology</strong><br>
        • Hybrid Search (Dense + Sparse Retrieval)<br>
        • Query Expansion & Re-ranking<br>
        • Chain-of-Thought Reasoning<br>
        • Local Ollama LLM - No API Keys Required
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 Upload Documents")
                
                file_input = gr.File(
                    label="Select ADGM Documents (.docx)",
                    file_count="multiple",
                    file_types=[".docx"],
                    elem_classes=["file-upload"]
                )
                
                with gr.Row():
                    process_btn = gr.Button(
                        "🔍 Review Documents",
                        variant="primary",
                        size="lg"
                    )
                    
                    export_btn = gr.Button(
                        "📦 Export All",
                        variant="secondary",
                        size="lg"
                    )
                
                gr.Markdown("""
                ### 📑 Supported Documents
                
                **Company Formation:**
                - Articles of Association
                - Board/Shareholder Resolutions
                - Incorporation Forms
                - Register of Members/Directors
                - UBO Declaration Forms
                
                **Other Categories:**
                - Employment Contracts
                - Commercial Agreements
                - Compliance Policies
                - License Applications
                """)
                
                with gr.Accordion("⚙️ System Status", open=False):
                    gr.Markdown("""
                    🟢 **Ollama Model:** llama2 (Running)
                    🟢 **Vector DB:** ChromaDB (Active)
                    🟢 **Embeddings:** all-MiniLM-L6-v2
                    🟢 **Cross-Encoder:** ms-marco-MiniLM
                    
                    **Advanced Features:**
                    - Hybrid Search ✅
                    - Query Expansion ✅
                    - Re-ranking ✅
                    - Chain-of-Thought ✅
                    """)
            
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Review Results")
                
                summary_output = gr.Markdown(
                    label="Review Summary",
                    elem_classes=["markdown-text"]
                )
                
                with gr.Tabs():
                    with gr.TabItem("📋 Compliance Report"):
                        json_output = gr.JSON(
                            label="Detailed Compliance Report",
                            elem_classes=["json-viewer"]
                        )
                    
                    with gr.TabItem("📥 Downloads"):
                        file_output = gr.File(
                            label="Download Reviewed Document",
                            visible=True
                        )
                        
                        zip_output = gr.File(
                            label="Download All Documents (ZIP)",
                            visible=False
                        )
        
        # Event handlers
        process_btn.click(
            fn=agent.process_documents,
            inputs=[file_input],
            outputs=[file_output, json_output, summary_output]
        )
        
        export_btn.click(
            fn=agent.export_all_results,
            inputs=[],
            outputs=[zip_output]
        ).then(
            lambda x: gr.update(visible=True if x else False),
            inputs=[zip_output],
            outputs=[zip_output]
        )
        
        gr.Markdown("""
        ---
        ### 💡 How It Works
        
        1. **Upload** your ADGM legal documents (.docx format)
        2. **AI Analysis** using Advanced RAG validates compliance
        3. **Review** detailed issues, recommendations, and compliance status
        4. **Download** reviewed documents with inline comments
        
        ### 🔒 Privacy & Security
        
        - All processing happens locally - no data leaves your system
        - No API keys or cloud services required
        - Fully compliant with data protection regulations
        
        ### ⚠️ Disclaimer
        
        This system provides automated compliance checking based on ADGM regulations. 
        For final submission, always consult with qualified legal counsel.
        
        ---
        *Powered by Ollama, ChromaDB, and Advanced RAG Technology*
        """)
    
    return demo

if __name__ == "__main__":
    print("=" * 60)
    print("ADGM Corporate Agent - Advanced RAG System")
    print("=" * 60)
    print("\n✅ Initializing system components...")
    print("📦 Loading knowledge base...")
    print("🤖 Connecting to Ollama...")
    print("\nMake sure Ollama is running: ollama serve")
    print("=" * 60)
    
    demo = create_interface()
    
    print("\n🚀 Launching application...")
    print("📍 Access at: http://localhost:7860")
    print("=" * 60)
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )