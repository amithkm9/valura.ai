# ===== 2. compliance_checker.py =====
"""
Compliance Checker Module
Validates documents against ADGM requirements
"""

class ComplianceChecker:
    """Check compliance with ADGM regulations"""
    
    def __init__(self):
        self.adgm_requirements = {
            "company_incorporation": {
                "required": [
                    "Articles of Association",
                    "Board Resolution", 
                    "Shareholder Resolution",
                    "Incorporation Application Form",
                    "Register of Members and Directors"
                ],
                "optional": [
                    "UBO Declaration Form",
                    "Memorandum of Association",
                    "Power of Attorney"
                ]
            },
            "licensing": {
                "required": [
                    "License Application Form",
                    "Business Plan",
                    "Compliance Manual",
                    "Board Resolution for License",
                    "Financial Projections"
                ],
                "optional": [
                    "Reference Letters",
                    "CV of Key Personnel"
                ]
            },
            "employment": {
                "required": [
                    "Employment Contract",
                    "Job Description",
                    "Salary Certificate"
                ],
                "optional": [
                    "Offer Letter",
                    "Non-Disclosure Agreement"
                ]
            }
        }
    
    def identify_process_type(self, document_names: list[str]) -> str:
        """Identify which ADGM process based on uploaded documents"""
        doc_names_lower = [name.lower() for name in document_names]
        
        # Check for incorporation documents
        incorporation_keywords = ["articles", "shareholder resolution", "board resolution", "incorporation", "register"]
        incorporation_matches = sum(1 for keyword in incorporation_keywords 
                                   if any(keyword in name for name in doc_names_lower))
        
        # Check for licensing documents
        licensing_keywords = ["license", "business plan", "compliance manual", "financial"]
        licensing_matches = sum(1 for keyword in licensing_keywords 
                                if any(keyword in name for name in doc_names_lower))
        
        # Check for employment documents
        employment_keywords = ["employment", "contract", "salary", "job description"]
        employment_matches = sum(1 for keyword in employment_keywords 
                                if any(keyword in name for name in doc_names_lower))
        
        # Return the process with most matches
        if incorporation_matches >= licensing_matches and incorporation_matches >= employment_matches:
            return "company_incorporation"
        elif licensing_matches >= employment_matches:
            return "licensing"
        else:
            return "employment"
    
    def check_missing_documents(self, uploaded_docs: list[str], process_type: str) -> dict:
        """Check for missing required documents"""
        if process_type not in self.adgm_requirements:
            return {
                "process": "unknown",
                "missing_documents": [],
                "uploaded_count": len(uploaded_docs),
                "required_count": 0
            }
        
        required_docs = self.adgm_requirements[process_type]["required"]
        uploaded_lower = [doc.lower() for doc in uploaded_docs]
        
        missing = []
        for required in required_docs:
            # Check if any uploaded document matches the required one
            found = False
            for uploaded in uploaded_lower:
                if any(keyword in uploaded for keyword in required.lower().split()):
                    found = True
                    break
            
            if not found:
                missing.append(required)
        
        return {
            "process": process_type,
            "missing_documents": missing,
            "uploaded_count": len(uploaded_docs),
            "required_count": len(required_docs)
        }
    
    def generate_recommendations(self, issues: list[dict], doc_check: dict) -> list[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Add recommendations for missing documents
        if doc_check.get("missing_documents"):
            recommendations.append(
                f"📄 Upload missing documents: {', '.join(doc_check['missing_documents'])}"
            )
        
        # Count issues by severity
        high_severity = sum(1 for issue in issues if issue.get("severity") == "high")
        medium_severity = sum(1 for issue in issues if issue.get("severity") == "medium")
        
        if high_severity > 0:
            recommendations.append(
                f"🔴 Address {high_severity} high-severity issues before submission"
            )
        
        if medium_severity > 0:
            recommendations.append(
                f"🟡 Review {medium_severity} medium-severity issues for compliance"
            )
        
        # Add specific recommendations based on common issues
        issue_types = set(issue.get("issue", "").split(":")[0] for issue in issues)
        
        if "Incorrect jurisdiction" in " ".join(issue_types):
            recommendations.append(
                "⚖️ Update all jurisdiction references to 'Abu Dhabi Global Market (ADGM)'"
            )
        
        if "Weak language" in " ".join(issue_types):
            recommendations.append(
                "📝 Replace weak language with binding terms (shall, must, will)"
            )
        
        if "Missing" in " ".join(issue_types):
            recommendations.append(
                "➕ Add all required sections as per ADGM templates"
            )
        
        return recommendations
