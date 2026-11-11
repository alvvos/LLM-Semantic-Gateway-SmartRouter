from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):

    # Ingeniería 
    status: str
    response: str
    similarity_score: Optional[float] = None

    # Lógica de negocio
    latency_sec: float
    cost_saved: bool