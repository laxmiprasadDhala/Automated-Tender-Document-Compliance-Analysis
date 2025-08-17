# --- Streamlit App UI ---
import streamlit as st
from scripts.extract_text import extract_text
from scripts.extract_requirements import extract_requirements_only, create_compliance_table_latex, evaluate_compliance
from scripts.compare_with_ollama import generate_comparison_table
import pandas as pd
import os

# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="Tender Comparison System")

st.title("📄 Tender Document Comparison System")
st.markdown(
    "Upload a tender document and up to three firm proposals to automatically compare their technical compliance and generate a report.")

# --- File Uploaders ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.header("Tender Document")
    tender_file = st.file_uploader("Upload Tender PDF", type="pdf", key="tender")

with col2:
    st.header("Firm 1 Proposal")
    firm1_file = st.file_uploader("Upload Firm 1 PDF", type="pdf", key="firm1")

with col3:
    st.header("Firm 2 Proposal")
    firm2_file = st.file_uploader("Upload Firm 2 PDF", type="pdf", key="firm2")

with col4:
    st.header("Firm 3 Proposal")
    firm3_file = st.file_uploader("Upload Firm 3 PDF", type="pdf", key="firm3")

# --- Analysis Trigger ---
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'tender_name' not in st.session_state:
    st.session_state.tender_name = ""

if st.button("🚀 Analyze and Compare Documents", use_container_width=True):
    st.session_state.analysis_complete = False
    st.session_state.report_data = None

    if not tender_file:
        st.warning("Please upload the main Tender Document to proceed.")
    else:
        firm_files = [f for f in [firm1_file, firm2_file, firm3_file] if f is not None]
        if not firm_files:
            st.warning("Please upload at least one Firm Proposal to compare.")
        else:
            with st.spinner("Step 1/4: Extracting text from all documents... This may take a moment."):
                tender_text = extract_text(tender_file)
                firm_texts = [extract_text(f) for f in firm_files]
                st.session_state.tender_name = tender_file.name

            if not tender_text:
                st.error("Could not extract text from the tender document. Cannot proceed.")
            else:
                with st.spinner("Step 2/4: Identifying technical requirements using AI..."):
                    requirements = extract_requirements_only(tender_text)

                if not requirements:
                    st.error("No technical requirements could be extracted from the tender document.")
                else:
                    with st.spinner("Step 3/4: Comparing each firm's proposal against requirements..."):
                        comparison_data = {"Requirement": requirements}
                        total_evaluations = len(requirements) * len(firm_texts)
                        progress_bar = st.progress(0, text="Evaluating compliance...")

                        for i, firm_text in enumerate(firm_texts):
                            firm_name = f"Firm {i + 1}"
                            compliance_results = []
                            for j, req in enumerate(requirements):
                                compliance = evaluate_compliance(req, firm_text)
                                compliance_results.append(compliance)
                                progress_value = ((i * len(requirements)) + j + 1) / total_evaluations
                                progress_text = f"Evaluating {firm_name} for requirement {j + 1}/{len(requirements)}"
                                progress_bar.progress(progress_value, text=progress_text)
                            comparison_data[firm_name] = compliance_results
                        progress_bar.empty()

                    with st.spinner("Step 4/4: Finalizing results..."):
                        df = pd.DataFrame(comparison_data)
                        st.session_state.report_data = df
                        st.session_state.analysis_complete = True
                        st.balloons()

# --- Display Results and Download Button ---
if st.session_state.analysis_complete:
    st.header("Analysis Results", divider='rainbow')
    df_results = st.session_state.report_data
    firm_names = [col for col in df_results.columns if col.startswith('Firm')]

    # --- Summary Statistics ---
    st.subheader("📈 Compliance Summary")
    summary_cols = st.columns(len(firm_names))
    for i, firm_col in enumerate(summary_cols):
        with firm_col:
            firm_name = firm_names[i]
            total_reqs = len(df_results)
            complied_count = df_results[firm_name].value_counts().get("Complied", 0)
            compliance_rate = (complied_count / total_reqs * 100) if total_reqs > 0 else 0
            st.metric(
                label=f"{firm_name} Compliance",
                value=f"{compliance_rate:.1f}%",
                delta=f"{complied_count} of {total_reqs} requirements met"
            )

    # --- Detailed Comparison Table ---
    st.subheader("📊 Detailed Compliance Comparison")


    def style_compliance(val):
        color = "green" if val == "Yes" else "red" if val == "No" else "orange"
        return f"color: {color}; font-weight: bold;"


    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "2.0/data")
    output_dir = os.path.join(base_dir, "2.0/output")
    
    firm1_path = os.path.join(data_dir, "firm_1.pdf")
    firm2_path = os.path.join(data_dir, "firm_2.pdf")
    firm3_path = os.path.join(data_dir, "firm_3.pdf")
    
    firm1_text = extract_text(firm1_path)
    firm2_text = extract_text(firm2_path)
    firm3_text = extract_text(firm3_path)
    latex_content = create_compliance_table_latex(requirements, firm1_text, firm2_text, firm3_text)

    st.dataframe(df_results.style.applymap(style_compliance, subset=firm_names), use_container_width=True)

    # --- Download Report ---
    st.subheader("📄 Download Report")
    st.markdown(
        "Download the complete analysis as a LaTeX (`.tex`) file. You can compile this into a PDF using a local LaTeX distribution (like MiKTeX or TeX Live).")

    report_filename = "tender_compliance_report.tex"
    report_filepath = os.path.join(output_dir, "requirements_compliance_report.tex")
    # Read the file content from the saved path for the download button
    with open(report_filepath, "r", encoding="utf-8") as f:
        file_data = f.read()

    st.download_button(
        label="📥 Download LaTeX Report (.tex)",
        data=file_data,
        file_name=report_filename,
        mime="text/x-tex",
        use_container_width=True
    )