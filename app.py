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

st.set_page_config(
    page_title="Legal Document Simplifier",
    layout="wide",
    page_icon="⚖️"
)

# Simple CSS for colored title and button
st.markdown("""
<style>
h1 {
    color: #1e40af;  /* A nice blue */
    font-weight: 700;
    text-align: center;
    margin-bottom: 1rem;
}
.stButton > button {
    background-color: #2563eb;
    color: white;
    font-weight: 600;
    padding: 0.6rem 2rem;
    border-radius: 8px;
    border: none;
    width: 100%;
    transition: background-color 0.3s ease;
}
.stButton > button:hover {
    background-color: #1d4ed8;
}
.qa-section {
    background-color: #f8fafc;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #2563eb;
    margin: 1rem 0;
}
.question {
    font-weight: 600;
    color: #1e40af;
    margin-bottom: 0.5rem;
}
.answer {
    color: #374151;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Legal Document Simplifier")

if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
    st.warning("⚠️ Invalid or missing GROQ_API_KEY. AI simplification will not work.")
if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    st.warning("⚠️ Missing GOOGLE_API_KEY or GOOGLE_CSE_ID. Advisor search will not work.")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
search_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

def call_llama_groq(prompt):
    if not client:
        return "GROQ API key missing, cannot process request."
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

def answer_question_about_document(question, document_text):
    """
    Answer a specific question about the given document using AI
    """
    if not client:
        return "GROQ API key missing, cannot answer questions."
    
    prompt = f"""
You are a legal assistant helping to answer questions about a specific legal document.

Here is the document content:
=== DOCUMENT START ===
{document_text}
=== DOCUMENT END ===

Question: {question}

Please provide a clear, accurate answer based solely on the information in the document above. If the document doesn't contain enough information to answer the question, please say so. Be specific and cite relevant sections when possible.

Answer:"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful legal assistant who answers questions based strictly on the provided document content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more focused answers
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error answering question: {e}"

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
    st.write("Upload a legal PDF document or paste legal text below, then click the button to simplify and get advisor recommendations.")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])
    with col2:
        text_input = st.text_area("Paste Legal Text Here", height=150)

    # Initialize session state for document text
    if 'document_text' not in st.session_state:
        st.session_state.document_text = ""
    if 'document_processed' not in st.session_state:
        st.session_state.document_processed = False

    if st.button("Simplify & Recommend Advisor"):
        if not uploaded_file and not text_input.strip():
            st.error("Please upload a PDF or enter legal text to continue.")
            return

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

        # Store document text in session state
        st.session_state.document_text = raw_text
        st.session_state.document_processed = True

        st.subheader("Original Input Preview")
        st.code(raw_text[:700] + ("..." if len(raw_text) > 700 else ""), language="text")

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
        st.write(simplified)

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

    # Q&A Section - only show if document has been processed
    if st.session_state.document_processed and st.session_state.document_text:
        st.markdown("---")
        st.subheader("🤖 Ask Questions About Your Document")
        st.write("You can now ask specific questions about the document you uploaded or pasted.")
        
        # Question input
        user_question = st.text_input(
            "Enter your question about the document:",
            placeholder="e.g., What are the key obligations mentioned in this contract?",
            key="question_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            ask_button = st.button("Ask Question", key="ask_btn")
        
        if ask_button and user_question.strip():
            with st.spinner("Analyzing document to answer your question..."):
                answer = answer_question_about_document(user_question, st.session_state.document_text)
            
            # Display Q&A in a styled format
            st.markdown(f"""
            <div class="qa-section">
                <div class="question">❓ {user_question}</div>
                <div class="answer">💡 {answer}</div>
            </div>
            """, unsafe_allow_html=True)
        
        elif ask_button and not user_question.strip():
            st.error("Please enter a question before clicking 'Ask Question'.")
        
        # Common question suggestions
        st.markdown("**💡 Suggested Questions:**")
        suggested_questions = [
            "What are the main parties involved in this document?",
            "What are the key terms and conditions?",
            "What are the important dates or deadlines mentioned?",
            "What are the payment terms or financial obligations?",
            "What happens if there's a breach of contract?",
            "Are there any termination clauses?",
            "What are the governing laws mentioned?"
        ]
        
        cols = st.columns(2)
        for i, question in enumerate(suggested_questions):
            with cols[i % 2]:
                if st.button(question, key=f"suggested_{i}"):
                    with st.spinner("Analyzing document to answer your question..."):
                        answer = answer_question_about_document(question, st.session_state.document_text)
                    
                    st.markdown(f"""
                    <div class="qa-section">
                        <div class="question">❓ {question}</div>
                        <div class="answer">💡 {answer}</div>
                    </div>
                    """, unsafe_allow_html=True)

    elif not st.session_state.document_processed:
        st.info("📄 Upload a document and click 'Simplify & Recommend Advisor' first to enable the Q&A feature.")

if __name__ == "__main__":
    main()