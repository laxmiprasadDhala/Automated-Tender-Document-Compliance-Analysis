# enhanced_extract_requirements.py

import ollama
import re
from typing import List, Dict


# def extract_requirements_only(tender_text: str, model="mistral:7b") -> List[str]:

def extract_requirements_only(tender_text: str, model="mistral:7b") -> list[str]:
    """
    Extract only the technical requirements from tender document using LLM
    """
    print("🔍 Extracting requirements from tender document...")

    system_prompt = """You are an expert AI assistant that extracts technical specifications from documents. Your 
    task is to identify and list only the technical requirements from the provided text.

    Focus on:
    - Hardware and software specifications (e.g., CPU, RAM, OS)
    - Performance requirements (e.g., speed, capacity)
    - Physical attributes (e.g., ports, dimensions)
    - Certifications and standards (e.g., ENERGY STAR, TCO-05)

    Ignore everything else, especially legal clauses, payment terms, and submission instructions.

    Output each requirement as a separate line, starting with a hyphen.

    Example output:
    - CPU: Intel Core i7-7700, 8MB L3 cache /Min 8 core/3.6GHz/ 65W, with Intel(R) Core(TM) i7 Label
    - Chipset: Intel® Q270 Chipset or better compactable with CPU
    - Memory: 8GB 2400MHz DDR4 Memory, RAM expandability up to 64 GB, (Memory slot should be 4 Min)
    - Monitor: 18.5” LED, TCO-05 CERTIFIED, SAME MAKE
    
    technical_keywords = [
                    'cpu', 'ram', 'memory', 'storage', 'hdd', 'ssd', 'ghz', 'mhz',
                    'gb', 'tb', 'mb', 'watts', 'voltage', 'power', 'usb', 'port',
                    'interface', 'compatible', 'specification', 'performance',
                    'capacity', 'speed', 'resolution', 'display', 'graphics',
                    'networking', 'ethernet', 'wifi', 'bluetooth', 'operating system',
                    'security', 'encryption', 'compliance', 'standard', 'certified'
                ]
    """

    user_prompt = f"""
Extract only those that looks like technical requirements from this tender document:

{tender_text}

Return only the requirements list, no other text.

"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    # Parse the response into individual requirements
    requirements_text = response['message']['content']
    print(requirements_text)
    requirements = []

    for line in requirements_text.split('\n'):
        # .strip(): This is a built-in Python method for strings. It creates a new string with all whitespace
        # characters (like spaces, tabs, and newlines) removed from the beginning and the end. It doesn't affect
        # whitespace in the middle of the string.
        line = line.strip()
        if line and (line.startswith('-') or line.startswith('•') or ':' in line):
            # Clean up the requirement text
            requirement = line.lstrip('- •').strip()
            if requirement:
                requirements.append(requirement)

    print(f"✅ Extracted {len(requirements)} requirements")

    return requirements
    # return requirements_text


def evaluate_compliance(requirement: str, firm_spec: str, model="mistral:7b") -> str:
    """
    Evaluate if a firm's specification complies with a specific requirement
    Returns 'Complied' or 'Not Complied'
    """
    system_prompt = """
You are a technical compliance evaluation expert. Compare a tender requirement with a firm's specification.

Rules for compliance:
- COMPLIED: If firm's spec meets or exceeds the requirement
- NOT COMPLIED: If firm's spec is below the requirement or missing

For technical specifications:
- Numbers: Firm's value should be ≥ minimum requirement
- Versions/Models: Firm's should be same or newer/better
- Certifications: Firm must have the required certifications
- Compatibility: Firm's solution must be compatible

Be strict but fair. If information is unclear or missing from firm spec, consider it NOT COMPLIED.

Respond with exactly one word: "Complied" or "Not Complied"
"""

    user_prompt = f"""
Requirement: {requirement}
Firm Specification Text: {firm_spec}

Evaluate compliance:
"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    result = response['message']['content'].strip()
    # Ensure we return standardized responses
    if "complied" in result.lower() and "not" not in result.lower():
        return "Complied"
    else:
        return "Not Complied"


def generate_compliance_comparison(requirements: List[str], firm1_text: str, firm2_text: str, firm3_text: str,
                                   model="mistral:7b") -> str:
    """
    Generate a detailed compliance comparison for all requirements
    """
    print("🔄 Evaluating compliance for all firms...")

    latex_rows = []

    for i, requirement in enumerate(requirements):
        print(f"📋 Evaluating requirement {i + 1}/{len(requirements)}")

        # Evaluate each firm's compliance
        firm1_compliance = evaluate_compliance(requirement, firm1_text)
        firm2_compliance = evaluate_compliance(requirement, firm2_text)
        firm3_compliance = evaluate_compliance(requirement, firm3_text)

        # Create LaTeX table row
        # Escape special LaTeX characters
        req_escaped = requirement.replace('&', '\\&').replace('%', '\\%').replace('_', '\\_').replace('#', '\\#')

        latex_row = f"{req_escaped} & {firm1_compliance} & {firm2_compliance} & {firm3_compliance} \\\\"
        latex_rows.append(latex_row)

    return "\n".join(latex_rows)


def create_compliance_table_latex(requirements: List[str], firm1_text: str, firm2_text: str, firm3_text: str) -> str:
    """
    Create complete LaTeX document with compliance table
    """
    # Generate compliance data
    table_rows = generate_compliance_comparison(requirements, firm1_text, firm2_text, firm3_text)

    latex_template = r"""
\documentclass[12pt]{article}
\usepackage{longtable}
\usepackage{array}
\usepackage[table]{xcolor}
\usepackage[a4paper, margin=0.8in]{geometry}
\usepackage{titlesec}
\renewcommand{\arraystretch}{1.3}
\setlength{\parskip}{6pt}
\titleformat{\section}{\normalfont\Large\bfseries}{}{0pt}{}

\begin{document}

\begin{center}
    \LARGE \textbf{Tender document comparison system}\\
\end{center}

\vspace{1cm}

\section*{Executive Summary}
This report presents a comprehensive compliance analysis of tender requirements against specifications submitted by three firms. Each requirement has been evaluated using AI-powered analysis to determine compliance status.

\section*{Methodology}
\begin{itemize}
    \item \textbf{Requirement Extraction:} AI-powered extraction of technical requirements from tender document
    \item \textbf{Compliance Evaluation:} Systematic comparison of firm specifications against each requirement  
    \item \textbf{Scoring:} Binary compliance assessment (Complied/Not Complied)
\end{itemize}

\section*{Compliance Analysis Results}

\begin{longtable}{|>{\raggedright\arraybackslash}p{7cm}|
                        >{\centering\arraybackslash}p{2.5cm}|
                        >{\centering\arraybackslash}p{2.5cm}|
                        >{\centering\arraybackslash}p{2.5cm}|}
\hline
\rowcolor{blue!20}
\textbf{Technical Requirement} & \textbf{Firm 1} & \textbf{Firm 2} & \textbf{Firm 3} \\
\hline
\endfirsthead

\hline
\rowcolor{blue!20}
\textbf{Technical Requirement} & \textbf{Firm 1} & \textbf{Firm 2} & \textbf{Firm 3} \\
\hline
\endhead

""" + table_rows + r"""

\hline
\end{longtable}

\section*{Legend}
\begin{itemize}
    \item \textbf{Complied:} Firm's specification meets or exceeds the tender requirement
    \item \textbf{Not Complied:} Firm's specification does not meet the tender requirement or information is missing
\end{itemize}

\section*{Recommendations}
Based on this automated compliance analysis, decision-makers should:
\begin{enumerate}
    \item Review firms with highest compliance rates
    \item Manually verify critical requirements marked as "Not Complied"
    \item Consider requesting clarifications for ambiguous specifications
    \item Evaluate cost-benefit for over-specified solutions
\end{enumerate}

\end{document}
"""
    return latex_template
