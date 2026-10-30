import time
import logfire
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings
from app.services.retrieval.embeddings import embed_query


# Initialize Qdrant Client with explicit timeout
client = QdrantClient(
    url=settings.QDRANT_CLUSTER_ENDPOINT,
    api_key=settings.QDRANT_API_KEY,
    timeout=settings.QDRANT_TIMEOUT
)

def search_enterprise_knowledge(query: str, limit: int = 8, max_retries: int = 2):
    """
    Performs a high-precision search in the enterprise knowledge base.
    Uses the modern query_points interface with retry logic for network resilience.
    """
    try:
        query_vector = embed_query(query)
    except Exception as e:
        logfire.error(f"❌ Query Embedding Failed: {e}")
        return []

    for attempt in range(max_retries + 1):
        try:
            with logfire.span(f"Qdrant Query Attempt {attempt + 1}"):
                response = client.query_points(
                    collection_name=settings.QDRANT_COLLECTION,
                    query=query_vector,
                    limit=limit,
                    with_payload=True,
                    timeout=settings.QDRANT_TIMEOUT
                )

            results = []
            for res in response.points:
                results.append({
                    "content": res.payload.get("text", ""),
                    "source": res.payload.get("source", "Unknown"),
                    "score": res.score
                })
            
            return results

        except Exception as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logfire.warning(f"⚠️ Qdrant search attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logfire.error(f"❌ Qdrant Search Failed after {max_retries + 1} attempts: {e}")
                return []