"""
Compliance Checker Module - Enhanced Version
Validates documents against ADGM requirements with improved accuracy
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
        
        # Document type mappings for better matching
        self.document_type_mappings = {
            "articles_of_association": "Articles of Association",
            "board_resolution": "Board Resolution",
            "shareholder_resolution": "Shareholder Resolution",
            "incorporation_application": "Incorporation Application Form",
            "register": "Register of Members and Directors",
            "memorandum": "Memorandum of Association",
            "ubo_declaration": "UBO Declaration Form",
            "employment_contract": "Employment Contract",
            "license_application": "License Application Form",
            "business_plan": "Business Plan",
            "compliance_manual": "Compliance Manual"
        }
    
    def identify_process_type(self, document_types: list[str]) -> str:
        """Identify which ADGM process based on document types"""
        
        # Convert document types to standard names
        standard_names = []
        for doc_type in document_types:
            # Check if it's a document type identifier
            for key, value in self.document_type_mappings.items():
                if key in doc_type.lower() or doc_type in value:
                    standard_names.append(value)
                    break
        
        # Check for incorporation documents
        incorporation_docs = self.adgm_requirements["company_incorporation"]["required"]
        incorporation_matches = sum(1 for doc in standard_names if doc in incorporation_docs)
        
        # Check for licensing documents
        licensing_docs = self.adgm_requirements["licensing"]["required"]
        licensing_matches = sum(1 for doc in standard_names if doc in licensing_docs)
        
        # Check for employment documents
        employment_docs = self.adgm_requirements["employment"]["required"]
        employment_matches = sum(1 for doc in standard_names if doc in employment_docs)
        
        # Return the process with most matches
        if incorporation_matches > 0:
            return "company_incorporation"
        elif licensing_matches > employment_matches:
            return "licensing"
        elif employment_matches > 0:
            return "employment"
        else:
            return "company_incorporation"  # Default to most common
    
    def check_missing_documents(self, uploaded_docs: list[str], process_type: str, 
                               document_types: list[str] = None) -> dict:
        """Enhanced missing document check using document types"""
        
        if process_type not in self.adgm_requirements:
            return {
                "process": "unknown",
                "missing_documents": [],
                "uploaded_count": len(uploaded_docs),
                "required_count": 0,
                "present_documents": []
            }
        
        required_docs = self.adgm_requirements[process_type]["required"]
        present_docs = []
        missing_docs = []
        
        # If we have document types, use them for more accurate matching
        if document_types:
            standard_names = []
            for doc_type in document_types:
                mapped_name = self.document_type_mappings.get(doc_type)
                if mapped_name:
                    standard_names.append(mapped_name)
            
            # Check which required documents are present
            for required in required_docs:
                if required in standard_names:
                    present_docs.append(required)
                else:
                    missing_docs.append(required)
        else:
            # Fallback to filename matching
            uploaded_lower = [doc.lower() for doc in uploaded_docs]
            
            for required in required_docs:
                found = False
                required_keywords = required.lower().split()
                
                for uploaded in uploaded_lower:
                    # Check if key terms from required doc name are in uploaded filename
                    matches = sum(1 for keyword in required_keywords 
                                if keyword in uploaded and len(keyword) > 3)
                    if matches >= len(required_keywords) * 0.5:  # At least 50% match
                        found = True
                        break
                
                if found:
                    present_docs.append(required)
                else:
                    missing_docs.append(required)
        
        return {
            "process": process_type,
            "missing_documents": missing_docs,
            "present_documents": present_docs,
            "uploaded_count": len(uploaded_docs),
            "required_count": len(required_docs)
        }
    
    def calculate_compliance_score(self, issues: list[dict], doc_check: dict) -> tuple[int, str]:
        """Calculate overall compliance score and status"""
        
        # Scoring weights
        weights = {
            "critical": -20,
            "high": -10,
            "medium": -5,
            "low": -2,
            "info": 0
        }
        
        # Start with perfect score
        score = 100
        
        # Deduct for issues
        for issue in issues:
            severity = issue.get("severity", "low")
            score += weights.get(severity, 0)
        
        # Deduct for missing documents (10 points each)
        missing_count = len(doc_check.get("missing_documents", []))
        score -= missing_count * 10
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        # Determine status
        if score >= 90:
            status = "PASS - Ready for submission"
        elif score >= 70:
            status = "REVIEW REQUIRED - Minor corrections needed"
        elif score >= 50:
            status = "FAIL - Significant corrections required"
        else:
            status = "CRITICAL - Major non-compliance detected"
        
        return score, status
    
    def generate_recommendations(self, issues: list[dict], doc_check: dict) -> list[str]:
        """Generate comprehensive compliance recommendations"""
        recommendations = []
        
        # Priority 1: Missing documents
        if doc_check.get("missing_documents"):
            missing_list = ", ".join(doc_check['missing_documents'])
            recommendations.append(
                f"📄 **URGENT**: Upload missing documents: {missing_list}"
            )
        
        # Priority 2: Critical and high-severity issues
        critical_count = sum(1 for issue in issues if issue.get("severity") == "critical")
        high_count = sum(1 for issue in issues if issue.get("severity") == "high")
        
        if critical_count > 0:
            recommendations.append(
                f"🚫 **CRITICAL**: Fix {critical_count} critical issues immediately"
            )
        
        if high_count > 0:
            recommendations.append(
                f"🔴 **HIGH PRIORITY**: Address {high_count} high-severity issues before submission"
            )
        
        # Priority 3: Common issue patterns
        issue_categories = {}
        for issue in issues:
            category = issue.get("issue", "").split(":")[0]
            if category not in issue_categories:
                issue_categories[category] = 0
            issue_categories[category] += 1
        
        # Specific recommendations based on issue patterns
        if "Incorrect jurisdiction" in issue_categories:
            recommendations.append(
                "⚖️ Update all jurisdiction references to 'Abu Dhabi Global Market (ADGM)'"
            )
        
        if "Weak language" in issue_categories:
            recommendations.append(
                "📝 Replace weak language (may, might, could) with binding terms (shall, must, will)"
            )
        
        if "Missing" in " ".join(issue_categories.keys()):
            recommendations.append(
                "➕ Add all required sections as per ADGM templates"
            )
        
        if "signature" in " ".join(issue_categories.keys()).lower():
            recommendations.append(
                "✍️ Complete all signature blocks with names, titles, and dates"
            )
        
        # Priority 4: Medium and low severity issues
        medium_count = sum(1 for issue in issues if issue.get("severity") == "medium")
        if medium_count > 0:
            recommendations.append(
                f"🟡 Review {medium_count} medium-severity issues for better compliance"
            )
        
        # Add positive feedback if applicable
        if not doc_check.get("missing_documents") and high_count == 0 and critical_count == 0:
            recommendations.append(
                "✅ Documents are largely compliant - review minor issues and submit"
            )
        
        return recommendations