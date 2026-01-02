#!/usr/bin/env python3
"""
Simple PDF to text converter script.
This script attempts to extract text from a PDF file using available libraries.
"""

import sys
import os

def extract_text_with_pypdf2(pdf_path):
    """Extract text using PyPDF2 library."""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text()
            return text
    except ImportError:
        return None
    except Exception as e:
        print(f"Error with PyPDF2: {e}")
        return None

def extract_text_with_pdfplumber(pdf_path):
    """Extract text using pdfplumber library."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text += f"\n--- Page {page_num + 1} ---\n"
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    except ImportError:
        return None
    except Exception as e:
        print(f"Error with pdfplumber: {e}")
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python pdf_converter.py <input_pdf> <output_txt>")
        print("Example: python pdf_converter.py 'Lesson 1 - Intro.pdf' 'lesson1.txt'")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    txt_path = sys.argv[2]
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)
    
    print(f"Attempting to convert '{pdf_path}' to '{txt_path}'...")
    
    # Try different PDF libraries
    text = extract_text_with_pypdf2(pdf_path)
    if text is None:
        text = extract_text_with_pdfplumber(pdf_path)
    
    if text is None:
        print("Error: No suitable PDF library found.")
        print("Please install PyPDF2 or pdfplumber:")
        print("  python -m pip install PyPDF2")
        print("  or")
        print("  python -m pip install pdfplumber")
        sys.exit(1)
    
    # Write extracted text to file
    try:
        with open(txt_path, 'w', encoding='utf-8') as output_file:
            output_file.write(text)
        print(f"Successfully converted PDF to text file: {txt_path}")
        print(f"Extracted {len(text)} characters from {pdf_path}")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
