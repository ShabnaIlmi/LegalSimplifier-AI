# Import necessary libraries
import os
import fitz  # PyMuPDF
import streamlit as st
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
import pytesseract
from groq import Groq
from googleapiclient.discovery import build

# Loading the environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Tesseract path 
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Page configuration with custom theme
st.set_page_config(
    page_title="Legal Document Simplifier", 
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="⚖️"
)

# Custom CSS for professional legal theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(30, 58, 138, 0.3);
    }
    
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-align: center;
        font-family: 'Inter', sans-serif;
    }
    
    .main-subtitle {
        color: #e2e8f0;
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(135deg, #065f46 0%, #059669 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.2rem;
        box-shadow: 0 4px 12px rgba(6, 95, 70, 0.3);
    }
    
    /* Warning boxes */
    .warning-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #92400e;
        font-weight: 500;
    }
    
    /* Success boxes */
    .success-box {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #065f46;
        font-weight: 500;
    }
    
    /* Error boxes */
    .error-box {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #991b1b;
        font-weight: 500;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1e40af 0%, #3730a3 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(30, 64, 175, 0.4);
    }
    
    /* File uploader styling */
    .uploadedFile {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 2px dashed #64748b;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Code block styling */
    .stCode {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 10px;
        border: 1px solid #475569;
    }
    
    /* Advisor cards */
    .advisor-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .advisor-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .advisor-title {
        color: #1e40af;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    .advisor-snippet {
        color: #64748b;
        line-height: 1.6;
    }
    
    /* Spinner styling */
    .stSpinner {
        color: #1e40af;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        .main-subtitle {
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Custom header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">⚖️ Legal Document Simplifier</h1>
    <p class="main-subtitle">Transform complex legal documents into clear, understandable language</p>
</div>
""", unsafe_allow_html=True)

# Validating the API keys and show warnings (don't stop to help debugging)
if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
    st.markdown('<div class="warning-box">⚠️ Invalid or missing GROQ_API_KEY. AI simplification will not work.</div>', unsafe_allow_html=True)
if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    st.markdown('<div class="warning-box">⚠️ Missing GOOGLE_API_KEY or GOOGLE_CSE_ID. Advisor search will not work.</div>', unsafe_allow_html=True)

# Initializing the clients only if keys present
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
search_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

def call_llama_groq(prompt):
    if not client:
        return "GROQ API key missing, cannot simplify document."
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a friendly AI legal assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling GROQ API: {e}"

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        if text.strip():
            return text
    except Exception:
        pass

    st.info("🔍 No text detected in PDF — performing OCR...")
    try:
        images = convert_from_bytes(pdf_bytes)
        ocr_text = "\n".join(pytesseract.image_to_string(img) for img in images)
        return ocr_text
    except Exception as e:
        st.markdown(f'<div class="error-box">❌ OCR failed: {e}</div>', unsafe_allow_html=True)
        return ""

def google_search(query, num=5):
    if not search_service:
        return []
    try:
        result = search_service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num).execute()
        return result.get("items", [])
    except Exception as e:
        st.markdown(f'<div class="error-box">❌ Google Search API error: {e}</div>', unsafe_allow_html=True)
        return []

def main():
    st.markdown("📄 Upload a legal PDF document or paste legal text below, then click the button to get started.")
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="section-header">📁 Upload Document</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], help="Upload your legal document in PDF format")
    
    with col2:
        st.markdown('<div class="section-header">✍️ Or Enter Text</div>', unsafe_allow_html=True)
        text_input = st.text_area("Paste your legal text here:", height=150, help="Copy and paste legal text directly")

    # Center the button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Simplify & Recommend Advisor"):
            if not uploaded_file and not text_input.strip():
                st.markdown('<div class="error-box">❌ Please upload a document or enter some text to proceed.</div>', unsafe_allow_html=True)
                return

            # Extracting text from PDF or use input text
            raw_text = ""
            source = ""
            if uploaded_file:
                source = "PDF document"
                with st.spinner("📖 Extracting text from PDF..."):
                    raw_text = extract_text_from_pdf(uploaded_file)
                if not raw_text.strip():
                    st.markdown('<div class="error-box">❌ Failed to extract any text from the PDF.</div>', unsafe_allow_html=True)
                    return
            else:
                source = "text input"
                raw_text = text_input.strip()

            st.markdown('<div class="section-header">📋 Original Input Preview</div>', unsafe_allow_html=True)
            st.code(raw_text[:500] + ("..." if len(raw_text) > 500 else ""), language="text")

            prompt = f"""
The following is a {source} containing legal language:

=== START ===
{raw_text}
=== END ===

Please:
1. Summarize the document in plain English.
2. Highlight key legal points and implications.
3. Suggest next steps and legal considerations, in a professional tone.
"""

            with st.spinner("🤖 Analyzing legal document with AI..."):
                simplified = call_llama_groq(prompt)

            st.markdown('<div class="section-header">📝 Simplified Summary</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="success-box">{simplified}</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">👨‍💼 Recommended Legal Advisors</div>', unsafe_allow_html=True)
            query = "legal advisor near me for contract law"
            with st.spinner("🔍 Searching for legal advisors..."):
                results = google_search(query, num=5)

            if results:
                for item in results:
                    title = item.get("title", "Unknown Title")
                    snippet = item.get("snippet", "No description available")
                    link = item.get("link", "#")
                    
                    st.markdown(f"""
                    <div class="advisor-card">
                        <div class="advisor-title">
                            <a href="{link}" target="_blank" style="text-decoration: none; color: #1e40af;">
                                🏛️ {title}
                            </a>
                        </div>
                        <div class="advisor-snippet">{snippet}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-box">⚠️ No legal advisors found or Google API keys missing.</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 2rem;">
        <p>⚖️ Legal Document Simplifier - Making legal documents accessible to everyone</p>
        <p><em>Disclaimer: This tool provides general information only and should not replace professional legal advice.</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()