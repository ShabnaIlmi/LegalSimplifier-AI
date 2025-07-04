import os
import fitz  # PyMuPDF
import streamlit as st
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
import pytesseract
from groq import Groq
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Set Tesseract path (for Windows users, change path if needed)
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Custom CSS for colors and styling
st.markdown(
    """
    <style>
    /* Background color */
    .main {
        background-color: #f0f4f8;
        color: #333333;
    }
    /* Title */
    h1 {
        color: #0a4471;
        font-weight: 700;
    }
    /* Headers */
    h2, h3 {
        color: #064663;
    }
    /* Button styling */
    div.stButton > button {
        background-color: #0a4471;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 18px;
        transition: background-color 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #064663;
        color: #e0e7ef;
    }
    /* Code block background */
    .stCodeBlock pre {
        background-color: #e8f0fe !important;
        color: #1a237e !important;
        border-radius: 6px !important;
        padding: 12px !important;
        font-size: 14px !important;
    }
    /* Info and warning boxes */
    .stAlert {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.set_page_config(page_title="Legal Document Simplifier", layout="wide")

st.title("⚖️ Legal Document Simplifier")
st.markdown(
    """
    Upload a **legal PDF document** or paste legal text, and get a **simplified summary** along with
    recommended **legal advisors** for your needs.
    """
)

if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
    st.warning("⚠️ Invalid or missing `GROQ_API_KEY`. AI simplification will not work.")
if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    st.warning("⚠️ Missing `GOOGLE_API_KEY` or `GOOGLE_CSE_ID`. Advisor search will not work.")

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

    st.info("No text detected in PDF — performing OCR...")
    try:
        images = convert_from_bytes(pdf_bytes)
        ocr_text = "\n".join(pytesseract.image_to_string(img) for img in images)
        return ocr_text
    except Exception as e:
        st.error(f"OCR failed: {e}")
        return ""

def google_search(query, num=5):
    if not search_service:
        return []
    try:
        result = search_service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num).execute()
        return result.get("items", [])
    except Exception as e:
        st.error(f"Google Search API error: {e}")
        return []

def main():
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Input")
        uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"], help="Upload a legal document in PDF format.")
        st.markdown("— OR —")
        text_input = st.text_area("Paste Legal Text Here", height=250, help="Or paste legal text for simplification.")
        run_button = st.button("Simplify & Recommend Advisor", type="primary")

    with col2:
        st.header("Output")

        if run_button:
            if not uploaded_file and not text_input.strip():
                st.error("Please upload a PDF or enter legal text to continue.")
                return

            if uploaded_file:
                with st.spinner("Extracting text from PDF..."):
                    raw_text = extract_text_from_pdf(uploaded_file)
                source = "PDF document"
            else:
                raw_text = text_input.strip()
                source = "text input"

            if not raw_text.strip():
                st.error("No text could be extracted from the input.")
                return

            st.subheader("Original Input Preview")
            st.code(raw_text[:700] + ("..." if len(raw_text) > 700 else ""), language="")

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

            with st.spinner("Analyzing legal document with AI..."):
                simplified = call_llama_groq(prompt)

            st.subheader("Simplified Summary")
            st.markdown(simplified)

            st.subheader("Recommended Legal Advisors")
            query = "legal advisor near me for contract law"
            with st.spinner("Searching for legal advisors..."):
                results = google_search(query, num=5)

            if results:
                for item in results:
                    title = item.get("title")
                    snippet = item.get("snippet")
                    link = item.get("link")
                    st.markdown(f"**[{title}]({link})**  \n{snippet}")
            else:
                st.info("No legal advisors found or missing Google API keys.")

if __name__ == "__main__":
    main()
