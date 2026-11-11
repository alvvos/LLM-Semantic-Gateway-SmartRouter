from fastapi import FastAPI
from src.api.router import router

app = FastAPI(
    title="LLMOps Semantic Gateway", 
    description="FinOps, control de latencia, y ahorro potencial"
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)