import streamlit as st
import fitz  
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from transformers import T5Tokenizer, T5ForConditionalGeneration, pipeline
import torch
import tempfile
from fpdf import FPDF

# MODEL AND TOKENIZER
checkpoint = "t5-small" 
tokenizer = T5Tokenizer.from_pretrained(checkpoint)
base_model = T5ForConditionalGeneration.from_pretrained(checkpoint)

# Risk Detection Functionality
risk_keywords = ["penalty", "breach", "compliance", "termination"]

def detect_risks(clauses):
    risks = []
    for clause in clauses:
        for keyword in risk_keywords:
            if keyword in clause.lower():
                risks.append(clause)
                break
    return risks

# Regulatory Update Tracker Functionality
def load_updates(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def match_updates_with_clauses(updates, clauses):
    flagged_clauses = []
    for update in updates:
        for clause in clauses:
            if update["law"].lower() in clause.lower():
                flagged_clauses.append((clause, update["law"]))
    return flagged_clauses

# Summarization
def llm_pipeline(input_text):
    pipe_sum = pipeline(
        'summarization',
        model=base_model,
        tokenizer=tokenizer,
        max_length=5000,
        min_length=200,
    )
    try:
        result = pipe_sum(input_text, truncation=True)
        return result[0]['summary_text']
    except Exception as e:
        return f"Error: Summarization failed. Details: {e}"

# Clean Text for PDF generation (handling special characters)
def clean_text(text):
    text = text.replace('\xa0', ' ')  
    text = text.replace('\u201c', '"').replace('\u201d', '"')  
    text = text.replace('\u2018', "'").replace('\u2019', "'")  
    return text

# Generate PDF with summarized text
def create_pdf(summary, file_path="summary.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Clean summary text to avoid encoding issues
    summary = clean_text(summary)
    
    pdf.multi_cell(0, 10, summary)
    pdf.output(file_path)
    return file_path

# Send email with PDF attachment
def send_email_with_pdf(recipient, summary):
    sender_email = "your_mail@gmail.com"  
    sender_password = "your app password"  

    subject = "Document Summary (PDF)"
    body = "Hello,\n\nPlease find attached the PDF document containing the summary of your document.\n\nBest regards,\nSummarization App"

    # Create the PDF
    pdf_path = create_pdf(summary)

    # Email setup
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF
    with open(pdf_path, "rb") as file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="summary.pdf"')
        msg.attach(part)

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return "Email with PDF sent successfully!"
    except Exception as e:
        return f"Error: {e}"

# Streamlit code
st.set_page_config(layout='wide', page_title="Summarization and Risk Detection App")

def main():
    st.title('Document Summarization and Risk Analysis App')

    uploaded_file = st.file_uploader("Upload your PDF File", type=['pdf'])
    recipient_email = st.text_input("Enter recipient email")
    summary = ""  

    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        # Preprocess document using PyMuPDF
        doc = fitz.open(temp_file_path)
        input_text = ""
        for page in doc:
            input_text += page.get_text()
        clauses = input_text.split("\n") if input_text else [] 

        col1, col2 = st.columns(2)

        with col1:
            st.info("Uploaded PDF File")

        # Summarization
        with col2:
            st.info("Document Summary")
            summary = llm_pipeline(input_text)
            if summary.startswith("Error:"):
                st.error(summary)
            else:
                st.write(summary)

        # Risk Detection
        st.subheader("Risk Detection")
        if clauses:
            risks = detect_risks(clauses)
            if risks:
                for risk in risks:
                    st.warning(risk)
            else:
                st.success("No risks detected!")
        else:
            st.error("No valid content detected for risk analysis!")

        # Regulatory Updates Check
        st.subheader("Regulatory Updates Check")
        try:
            regulatory_updates = load_updates("regulatory_updates.json")  
            flagged_clauses = match_updates_with_clauses(regulatory_updates, clauses)
            if flagged_clauses:
                for clause, law in flagged_clauses:
                    st.error(f"Clause: {clause} - Requires update for: {law}")
            else:
                st.success("All clauses are compliant!")
        except Exception as e:
            st.error(f"Error in regulatory updates check: {e}")

        # Key Clauses
        st.subheader("Key Clauses")
        for clause in clauses:
            st.write(clause)

        # Send Email
        if recipient_email:
            if st.button("Send Summary by Email"):
                email_status = send_email_with_pdf(recipient_email, summary)
                if email_status.startswith("Error:"):
                    st.error(email_status)
                else:
                    st.success(email_status)

if __name__ == '__main__':
    main()
