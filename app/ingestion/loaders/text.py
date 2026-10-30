import logfire

def parse_text(file_path:str)->str:
    """
    Parse plain text files
    """
    with logfire.span("Parsing text file", filename=file_path):
        try:
            with open(file_path,"r",encoding="utf-8") as f:
                text = f.read()
            logfire.info(f"Read {len(text)} chars from {file_path}")
            return text
        except Exception as e:
            logfire.error("Failed to parse text file",error=str(e),filename=file_path)
            raise