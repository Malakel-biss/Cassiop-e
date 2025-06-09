# main_app/ai_assistant/pdf_parser.py

from PyPDF2 import PdfReader
import os

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"  # Extract text from each page
        return text.strip()
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None
