# generate_report.py

import os
from extract_text import extract_text
from extract_requirements import extract_requirements_only, create_compliance_table_latex
from compare_with_ollama import extract_structured_requirements
import subprocess

# Define directories
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.join(base_dir, "data")
output_dir = os.path.join(base_dir, "output")


def compile_latex_to_pdf(tex_path, output_dir2):
    """Compiles a .tex file to a .pdf using pdflatex."""
    try:
        # Run pdflatex twice for proper formatting
        process = subprocess.run(
            ["pdflatex", "-output-directory", output_dir2, tex_path],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ First compilation pass complete.")

        process = subprocess.run(
            ["pdflatex", "-output-directory", output_dir2, tex_path],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Second compilation pass complete.")

        pdf_name = os.path.basename(tex_path).replace(".tex", ".pdf")
        pdf_path = os.path.join(output_dir2, pdf_name)
        print(f"🎉 Successfully generated PDF: {pdf_path}")

    except FileNotFoundError:
        print("❌ Error: 'pdflatex' command not found.")
        print("👉 Please install a LaTeX distribution (like MiKTeX, TeX Live) and ensure it's in your system's PATH.")
    except subprocess.CalledProcessError as e:
        print(f"❌ LaTeX compilation failed with error:\n{e.stdout}\n{e.stderr}")


def calculate_compliance_summary(latex_content: str) -> dict:
    """Calculate compliance statistics from the generated table"""
    lines = latex_content.split('\n')

    firm1_complied = 0
    firm2_complied = 0
    firm3_complied = 0
    total_requirements = 0

    for line in lines:
        if '&' in line and 'Complied' in line:
            total_requirements += 1
            parts = line.split('&')
            if len(parts) >= 4:
                if 'Complied' in parts[1] and 'Not Complied' not in parts[1]:
                    firm1_complied += 1
                if 'Complied' in parts[2] and 'Not Complied' not in parts[2]:
                    firm2_complied += 1
                if 'Complied' in parts[3] and 'Not Complied' not in parts[3]:
                    firm3_complied += 1

    return {
        'total_requirements': total_requirements,
        'firm1_compliance': (firm1_complied / total_requirements * 100) if total_requirements > 0 else 0,
        'firm2_compliance': (firm2_complied / total_requirements * 100) if total_requirements > 0 else 0,
        'firm3_compliance': (firm3_complied / total_requirements * 100) if total_requirements > 0 else 0,
        'firm1_complied': firm1_complied,
        'firm2_complied': firm2_complied,
        'firm3_complied': firm3_complied
    }


def main(firm_1_text=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("📄 Extracting text from PDFs...")
    tender_path = os.path.join(data_dir, "tender.pdf")
    firm1_path = os.path.join(data_dir, "firm_1.pdf")
    firm2_path = os.path.join(data_dir, "firm_2.pdf")
    firm3_path = os.path.join(data_dir, "firm_3.pdf")

    # Check if all files exist
    required_files = [tender_path, firm1_path, firm2_path, firm3_path]
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Error: File not found: {file_path}")
            return

    tender_text = extract_text(tender_path)
    firm1_text = extract_text(firm1_path)
    firm2_text = extract_text(firm2_path)
    firm3_text = extract_text(firm3_path)
    print("✅ Text extraction complete.\n")
    # print(tender_text)

    print("🔍 Extracting requirements from tender document...")
    # requirements = extract_requirements_only(tender_text)
    requirements = extract_requirements_only(tender_text)
    print(requirements)

    if not requirements:
        print("❌ No requirements found in tender document. Please check the document content.")
        return

    print(f"✅ Found {len(requirements)} requirements")
    print("\n📋 Extracted Requirements Preview:")
    for i, req in enumerate(requirements[:5], 1):  # Show first 5 requirements
        print(f"  {i}. {req[:80]}{'...' if len(req) > 80 else ''}")
    if len(requirements) > 5:
        print(f"  ... and {len(requirements) - 5} more requirements")
    print()

    print("🤖 Generating compliance analysis using Mistral...")
    latex_content = create_compliance_table_latex(requirements, firm1_text, firm2_text, firm3_text)
    print("✅ Compliance analysis complete.\n")

    # Calculate and display summary statistics
    stats = calculate_compliance_summary(latex_content)
    print("📊 Compliance Summary:")
    print(f"   Total Requirements Analyzed: {stats['total_requirements']}")
    print(f"   Firm 1: {stats['firm1_complied']}/{stats['total_requirements']} ({stats['firm1_compliance']:.1f}%)")
    print(f"   Firm 2: {stats['firm2_complied']}/{stats['total_requirements']} ({stats['firm2_compliance']:.1f}%)")
    print(f"   Firm 3: {stats['firm3_complied']}/{stats['total_requirements']} ({stats['firm3_compliance']:.1f}%)")
    print()

    print("📄 Generating LaTeX report...")
    output_path = os.path.join(output_dir, "requirements_compliance_report.tex")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(latex_content)

    print(f"✅ LaTeX file saved to: {output_path}")

    # Compile to PDF
    # if os.path.exists(output_path):
    #     print("\n🔄 Compiling LaTeX to PDF...")
    #     compile_latex_to_pdf(output_path, output_dir)
    #
    # print("\n🎉 Process completed successfully!")
    # print(f"📁 Check the output directory: {output_dir}")


if __name__ == "__main__":
    main()
