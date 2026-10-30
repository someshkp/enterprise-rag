from bs4 import BeautifulSoup 
import logfire

def parse_html(file_path:str):
    """
    Parse HTML content using beautiful soup
    Cleadn scripts, styles, and extract readable content for RAG.
    """
    with logfire.span("HTML Parsing", filename=file_path):
        try:
            with open(file_path,'r',encoding='utf-8',errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content,"html.parser")

            # Remove junk (scripts, style, metadata)
            for tag in soup(["script", "style", "meta", "noscript"]):
                tag.decompose()
                
            #2. Extract text
            text = soup.get_text(separator=" \n ")

            #3. Clean and normalize text
            lines =(line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
            text_clean = '\n'.join(chunk for chunk in chunks if chunk)

            return text_clean
        
        except Exception as e:
            logfire.error("Failed to parse HTML file", error=str(e), filename=file_path)
            raise
            
    