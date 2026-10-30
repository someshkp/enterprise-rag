import logfire
from unstructured.partition.auto import partition

def parse_office(file_path:str):
    """
    Parse Office docs (.docx, .pptx, .msg) using unstructured partition
    """
    with logfire.span("Office Document Parsing",filename=file_path):
        try:
            elements= partition(filename=file_path)
            full_text = "\n".join([str(el) for el in elements])
            
            if not full_text.strip():
                logfire.warn("Office doc contains no text",filename=file_path)
            else:
                logfire.info("Office doc parsed successfully",filename=file_path)
            return full_text
        except Exception as e:
            logfire.error("Failed to parse Office file",error=str(e),filename=file_path)
            raise
        