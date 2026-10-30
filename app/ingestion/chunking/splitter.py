from typing import List
import logfire

def chunk_text(text:str, chunk_size:int=1500)-> List[str]:
    """
    Simple semantic-ish chunker that splits by paragraphs.
    Ensures chunks do not exceed the specified size.
    """
    
    with logfire.span("Text Chunking", text_length=len(text)):
        if not text.strip():
            return []
        
        paragraphs = text.split('\n\n')
        chunks=[]
        current_chunk=""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += "\n\n" + para
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks