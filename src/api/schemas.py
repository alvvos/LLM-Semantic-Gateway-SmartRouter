
from pydantic import BaseModel


class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):

    # Ingeniería 
    status: str
    response: str
    similarity_score: float | None = None

    # Lógica de negocio
    latency_sec: float
    cost_saved: bool