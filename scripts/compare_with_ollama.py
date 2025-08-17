# updated_compare_with_ollama.py

import ollama
import re
from typing import List, Dict, Tuple


def extract_structured_requirements(tender_text: str, model="mistral:7b") -> List[Dict[str, str]]:
    """
    Extract requirements in a structured format with categories
    """
    print("🔍 Extracting structured requirements...")

    system_prompt = """
You are a technical requirements extraction specialist. Extract ONLY technical requirements from tender documents.

Output format - each requirement on a new line as:
CATEGORY: Requirement description: Specific value/criteria

Categories to use:
- HARDWARE: Physical components, devices
- SOFTWARE: Applications, OS, programming
- PERFORMANCE: Speed, capacity, throughput  
- ELECTRICAL: Voltage, power, current
- PHYSICAL: Dimensions, weight, materials
- ENVIRONMENTAL: Temperature, humidity, protection
- CONNECTIVITY: Ports, wireless, networking
- CERTIFICATION: Standards, compliance, testing
- QUALITY: Reliability, durability, warranty

Example output:
HARDWARE: Processor: Intel i7 10th gen or equivalent
ELECTRICAL: Operating Voltage: 230V ±10%  
PERFORMANCE: Processing Speed: Minimum 3.0 GHz
ENVIRONMENTAL: Operating Temperature: -20°C to +60°C
CERTIFICATION: Compliance: CE, FCC, RoHS required

Extract only technical specifications, ignore legal/commercial terms.
"""

    user_prompt = f"""
Extract technical requirements from this tender document:

{tender_text}

Return only the structured requirements list.
"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    requirements = []
    lines = response['message']['content'].split('\n')
    print(lines)

    for line in lines:
        line = line.strip()
        if ':' in line and any(cat in line.upper() for cat in
                               ['HARDWARE', 'SOFTWARE', 'PERFORMANCE', 'ELECTRICAL', 'PHYSICAL', 'ENVIRONMENTAL',
                                'CONNECTIVITY', 'CERTIFICATION', 'QUALITY']):
            parts = line.split(':', 2)
            if len(parts) >= 3:
                category = parts[0].strip()
                requirement = parts[1].strip()
                specification = parts[2].strip()

                requirements.append({
                    'category': category,
                    'requirement': requirement,
                    'specification': specification,
                    'full_text': f"{requirement}: {specification}"
                })

    print(f"✅ Extracted {len(requirements)} structured requirements")
    return requirements


def smart_compliance_check(requirement_spec: str, firm_spec: str, model="mistral:7b") -> Tuple[str, str]:
    """
    Intelligent compliance checking with reasoning
    """
    system_prompt = """
You are a technical compliance expert. Evaluate if a firm's specification meets a tender requirement.

Evaluation Rules:
1. NUMERICAL VALUES: Firm must meet or exceed minimum requirements
2. VERSIONS/MODELS: Firm's version should be same or newer
3. CERTIFICATIONS: Firm must explicitly have required certifications  
4. COMPATIBILITY: Firm's solution must be compatible with specified standards
5. MISSING INFO: If firm doesn't mention the requirement, consider "Not Complied"

Response format:
STATUS: [Complied/Not Complied]
REASON: [Brief explanation why]

Be precise and strict in evaluation.
"""

    user_prompt = f"""
Tender Requirement: {requirement_spec}
Firm Specification: {firm_spec}

Evaluate compliance:
"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    result = response['message']['content']

    # Parse response
    status = "Not Complied"  # Default
    reason = "Unable to determine compliance"

    if "STATUS:" in result:
        status_line = [line for line in result.split('\n') if 'STATUS:' in line][0]
        status = status_line.split('STATUS:')[1].strip()

    if "REASON:" in result:
        reason_line = [line for line in result.split('\n') if 'REASON:' in line][0]
        reason = reason_line.split('REASON:')[1].strip()

    # Standardize status
    if "complied" in status.lower() and "not" not in status.lower():
        status = "Complied"
    else:
        status = "Not Complied"

    return status, reason


def generate_enhanced_comparison_table(tender_text: str, firm1_text: str, firm2_text: str, firm3_text: str,
                                       model="mistral") -> str:
    """
    Generate enhanced comparison with structured requirements
    """
    print("🧠 Using enhanced model:", model)

    # Extract structured requirements
    requirements = extract_structured_requirements(tender_text, model)

    if not requirements:
        print("❌ No requirements found!")
        return ""

    latex_rows = []

    print(f"🔄 Evaluating {len(requirements)} requirements across 3 firms...")

    for i, req in enumerate(requirements):
        print(f"📋 Processing requirement {i + 1}/{len(requirements)}: {req['requirement']}")

        # Evaluate compliance for each firm
        firm1_status, firm1_reason = smart_compliance_check(req['full_text'], firm1_text, model)
        firm2_status, firm2_reason = smart_compliance_check(req['full_text'], firm2_text, model)
        firm3_status, firm3_reason = smart_compliance_check(req['full_text'], firm3_text, model)

        # Escape LaTeX special characters
        req_text = req['full_text'].replace('&', '\\&').replace('%', '\\%').replace('_', '\\_').replace('#',
                                                                                                        '\\#').replace(
            '$', '\\$')

        # Color code the compliance status
        firm1_cell = f"\\textcolor{{{'green' if firm1_status == 'Complied' else 'red'}}}{{{firm1_status}}}"
        firm2_cell = f"\\textcolor{{{'green' if firm2_status == 'Complied' else 'red'}}}{{{firm2_status}}}"
        firm3_cell = f"\\textcolor{{{'green' if firm3_status == 'Complied' else 'red'}}}{{{firm3_status}}}"

        latex_row = f"{req_text} & {firm1_cell} & {firm2_cell} & {firm3_cell} \\\\"
        latex_rows.append(latex_row)

        # Add horizontal line between categories
        if i < len(requirements) - 1 and requirements[i]['category'] != requirements[i + 1]['category']:
            latex_rows.append("\\hline")

    return "\n".join(latex_rows)


# Legacy function for backward compatibility
def generate_comparison_table(tender_text, firm1_text, firm2_text, firm3_text, model="mistral"):
    """
    Legacy function - calls the enhanced version
    """
    return generate_enhanced_comparison_table(tender_text, firm1_text, firm2_text, firm3_text, model)