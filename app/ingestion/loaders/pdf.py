from pypdf import PageObject
import enum
import logfire
from pypdf import PdfReader

def parse_pdf(file_path:str)->str:
    """
    Parse a PDF file using PyPDF
    Returns full text content
    """
    with logfire.span("PDF parsing (local)", filename=file_path):
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            logfire.info("PDF has {total_pages} pages",filename=file_path)
            
            text_parts:list[str]=[]
            blank_pages:list[str] = []
          
            for i, page in enumerate[PageObject](reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    text_parts.append(text)
                else:
                    blank_pages.append(i+1)
                    
            if blank_pages:           
                logfire.info("Found {len(blank_pages)} blank pages",filename=file_path)
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        for page_num in blank_pages:
                            page = pdf.pages[page_num-1]
                            fallback_text=page.extract_text() or ""
                            if fallback_text.strip():
                                text_parts.append(fallback_text)
                except Exception as plumber_err:
                    logfire.error(f"Pdfplumber fallback failed {plumber_err}")
            full_text = "\n".join(text_parts)
            
            if not full_text.strip():
                logfire.error(f"No text extracted from {file_path}. File may be fully image-based")
            else:
                logfire.info(f"Extracted {len(full_text)} chars from {file_path}")
            
            return full_text
        except Exception as e:
            logfire.error("Failed to parse PDF",error=str(e),filename=file_path)
            raise
    
    