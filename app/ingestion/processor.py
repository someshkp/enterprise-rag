import os 
import sys
import uuid
import json
import logfire

from qdrant_client import QdrantClient
from qdrant_client.http import models


from app.config import settings
from app.services.retrieval.embeddings import embed_text,get_embedding_dim
from app.ingestion.chunking.splitter import chunk_text
from app.ingestion.loaders.text import parse_text
from app.ingestion.loaders.html import parse_html
from app.ingestion.loaders.office import parse_office
from app.ingestion.loaders.pdf import parse_pdf

logfire.configure(service_name="enterprise-ingestion-service")

PROCESSED_DATA_DIR = "processed_data"

## Initialize qdrant client
qdrant_client=QdrantClient(
    url=settings.QDRANT_CLUSTER_ENDPOINT,
    api_key=settings.QDRANT_API_KEY
)

def save_processed_locally(data: dict,source_type: str, filename: str) -> str:
    """save parse chunk metadata as JSON in processed_data/<source_type>/."""
    # Ensure directory exists
    folder = os.path.join(PROCESSED_DATA_DIR,source_type)
    os.makedirs(folder,exist_ok=True)
    dest = os.path.join(folder,f"{filename}.json")
    with open(dest,"w",encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logfire.info("File saved locally",path=dest)
    return dest

def process_file(file_path:str,filename:str,source_type: str):
    """Parse -> chunk -> save locally -> embed -> index in qdrant"""
    with logfire.span("Processing file",file=filename,source=source_type):
        try:
            ext = filename.lower().rsplit(".",1)[-1]
            if ext == "pdf":
                full_text = parse_pdf(file_path)
            elif ext in ["doc", "docx", "ppt", "pptx", "msg"]:
                full_text = parse_office(file_path)
            elif ext == "txt":
                full_text = parse_text(file_path)
            elif ext in ["html", "htm"]:
                full_text = parse_html(file_path)
            else:
                logfire.info("Skipping unsupported file type")    
                return 
            
            if not full_text or not full_text.strip():
                logfire.warning("No text extracted", file=filename) 
                return

            chunks = chunk_text(full_text)

            if not chunks:
                logfire.warning("No chunks created", file=filename)
                return
             
            processed_data = {
                "filename": filename,
                "source_type": source_type,
                "chunks": chunks
            }

            local_path = save_processed_locally(processed_data, source_type, filename)
            logfire.info(f"File processed successfully -> {local_path}")
            
            with logfire.span("Vectorizing & Indexing"):
                embedding = embed_text(chunks)
                points = [
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                          "text": chunk,
                          "source": filename,
                          "source_type": source_type,                       
                        }
                    )
                    for chunk, vector in zip(chunks, embedding)
                ]
                
                qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION,
                    points=points
                )

                logfire.info(f"Indexed {len(points)} chunks from {filename}")
            
        except Exception as e:
            logfire.error("Failed to process file",file=filename,error=str(e))
            

def process_directory(dir_path:str, source_type:str):
    """Porcess every file in the directory"""
    with logfire.span("Scanning Directory", path=dir_path, source=source_type):
        files= [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,f))]
        logfire.info("Found files",count=len(files))
        for filename in files:
            file_path = os.path.join(dir_path,filename)
            process_file(file_path,filename,source_type)

def run_universal_ingestion(base_dir:str, explicit_source_type:str=None, wipe: bool =False):
    """
    Scan base_dir, map sub folders to source types, and ingest all document.
    Pass - wipe to dropand recreate the Qdrant collection before ingestion.
    """
    with logfire.span("Universal Ingestion Started ", base_dir=base_dir, explicit_source=explicit_source_type, wipe=wipe):
        if wipe and qdrant_client.collection_exists(settings.QDRANT_COLLECTION):
            qdrant_client.delete_collection(settings.QDRANT_COLLECTION)
            logfire.info("Wiped existing Qdrant collection", collection_name=settings.QDRANT_COLLECTION)

        if not qdrant_client.collection_exists(settings.QDRANT_COLLECTION):
            dim = get_embedding_dim()
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=64
                )
            )
            logfire.info("Created new Qdrant collection", collection_name=settings.QDRANT_COLLECTION)
        
        subdirs = [
            d for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d))
        ]
        
        if not subdirs:
            if explicit_source_type:
                source_type = explicit_source_type
            else:
                base_name=os.path.basename(os.path.normpath(base_dir)).lower()
                source_type= (
                    "true" if "true" in base_name
                    else "noisy" if "noisy" in base_name
                    else "general"
                )
            logfire.info(f"No sub-folders found - processing '{base_dir}' as {source_type}")
            process_directory(base_dir, source_type)
        else:
            for subdir in subdirs:
                source_type = (
                    "true" if "true" in subdir.lower()
                    else "noisy" if "noisy" in subdir.lower()
                    else "general"
                )
                process_directory(os.path.join(base_dir, subdir), source_type)


if __name__ == "__main__":
    # Usage:
    #   python -m app.ingestion.processor DATA --wipe
    #   python -m app.ingestion.processor DATA/true_data true
    wipe_requested = "--wipe" in sys.argv
    clean_args = [a for a in sys.argv if a != "--wipe"]
    
    target_dir = clean_args[1] if len(clean_args)>1 else "DATA"
    explicit_type = clean_args[2] if len(clean_args)>2 else None
    if not os.path.exists(target_dir):
        print(f"Error:path '{target_dir}' doest not exist. Please provide a valid path.")
        sys.exit(1)

    run_universal_ingestion(target_dir,explicit_source_type=explicit_type,wipe=wipe_requested)
    logfire.info("Ingestion job completed.")    