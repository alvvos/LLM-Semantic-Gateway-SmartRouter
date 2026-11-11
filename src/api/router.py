import time

from fastapi import APIRouter

from src.api.schemas import QueryRequest, QueryResponse
from src.core.redis_cache import cache_instance

router = APIRouter()

def call_expensive_llm(prompt: str) -> str:
    """
    Simula la llamada a un modelo pesado y de pago (e.g. GPT-4o).
    En un entorno real, aquí usaríamos el SDK de OpenAI o LangChain.
    """
    time.sleep(1.5)
    return f"[Generado por LLM de pago] Respuesta para: '{prompt}'"


@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(req: QueryRequest):

    start_time = time.time()
    cached_response, score = cache_instance.search(req.prompt)
    
    # Caso 1: Era una pregunta ya hecha
    if cached_response:
        latency = time.time() - start_time
        return QueryResponse(
            status="CACHE_HIT",
            response=cached_response,
            similarity_score=round(float(score), 4),
            latency_sec=round(latency, 4),
            cost_saved=True
        )
        
    # Caso 2: El mensaje no está en caché
    llm_response = call_expensive_llm(req.prompt)
    cache_instance.add(req.prompt, llm_response)
    
    total_latency = time.time() - start_time
    return QueryResponse(
        status="CACHE_MISS (LLM Called)",
        response=llm_response,
        latency_sec=round(total_latency, 4),
        similarity_score=round(float(score), 4) if score > 0 else None,
        cost_saved=False
    )