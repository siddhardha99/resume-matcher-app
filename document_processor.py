import streamlit as st
import PyPDF2
import docx
import io

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(docx_file):
    """Extract text from a DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(docx_file.read()))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from DOCX: {e}")
        return ""

def process_resume_file(resume_file):
    """Process the uploaded resume file and extract text"""
    if resume_file is None:
        return ""
        
    # Extract text from resume based on file type
    file_type = resume_file.name.split('.')[-1].lower()
    
    try:
        if file_type == "txt":
            # Reset file pointer and read
            resume_file.seek(0)
            resume_text = resume_file.read().decode("utf-8")
            st.success("Text file processed successfully!")
            return resume_text
            
        elif file_type == "pdf":
            # Reset file pointer and process
            resume_file.seek(0)
            resume_text = extract_text_from_pdf(resume_file)
            if resume_text:
                st.success("PDF processed successfully!")
                # Show the extracted text in an expander
                with st.expander("View extracted text"):
                    st.text(resume_text)
                # Allow user to edit if needed
                resume_text = st.text_area("Edit extracted text if needed:", value=resume_text, height=200)
                return resume_text
                
        elif file_type == "docx":
            # Reset file pointer and process
            resume_file.seek(0)
            resume_text = extract_text_from_docx(resume_file)
            if resume_text:
                st.success("DOCX processed successfully!")
                # Show the extracted text in an expander
                with st.expander("View extracted text"):
                    st.text(resume_text)
                # Allow user to edit if needed
                resume_text = st.text_area("Edit extracted text if needed:", value=resume_text, height=200)
                return resume_text
                
        else:
            st.error(f"Unsupported file type: {file_type}")
            return ""
            
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return ""