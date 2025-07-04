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
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

st.set_page_config(page_title="Legal Document Simplifier", layout="centered")
st.title("Legal Document Simplifier")

# Validate API keys and show warnings (don't stop to help debugging)
if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
    st.warning("⚠️ Invalid or missing `GROQ_API_KEY`. AI simplification will not work.")
if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    st.warning("⚠️ Missing `GOOGLE_API_KEY` or `GOOGLE_CSE_ID`. Advisor search will not work.")

# Initialize clients only if keys present
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
        # Use getvalue once, avoid read() multiple times which breaks the stream
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
    st.markdown("Upload a legal PDF document or paste legal text below, then click **Simplify & Recommend Advisor**.")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    text_input = st.text_area("Or paste your legal text here:", height=200)

    if st.button("Simplify & Recommend Advisor"):
        if not uploaded_file and not text_input.strip():
            st.error("Please upload a document or enter some text to proceed.")
            return

        # Extract text from PDF or use input text
        raw_text = ""
        source = ""
        if uploaded_file:
            source = "PDF document"
            with st.spinner("Extracting text from PDF..."):
                raw_text = extract_text_from_pdf(uploaded_file)
            if not raw_text.strip():
                st.error("Failed to extract any text from the PDF.")
                return
        else:
            source = "text input"
            raw_text = text_input.strip()

        st.subheader("Original Input (preview)")
        st.code(raw_text[:500] + ("..." if len(raw_text) > 500 else ""))

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
            st.info("No legal advisors found or Google API keys missing.")

if __name__ == "__main__":
    main()
