# Semantic LLM Gateway

Repositorio de implementación de un patrón arquitectónico *Semantic Gateway* para la interceptación inteligente de peticiones a Modelos de Lenguaje Grande (LLMs). Diseñado bajo principios de FinOps, LLMOps y observabilidad, este sistema minimiza la latencia y reduce los costes operativos de inferencia mediante caché vectorial distribuida.

## Visión general

En entornos empresariales con alta concurrencia de usuarios interactuando con modelos fundacionales, una proporción significativa de las consultas posee una intención semántica idéntica, aunque difiera en su estructura sintáctica. 

Este gateway actúa como un proxy inverso inteligente que:
1. Vectoriza la consulta entrante utilizando modelos de *embeddings* locales de baja latencia.
2. Realiza una búsqueda de similitud del coseno (*K-Nearest Neighbors*) en un clúster de Redis.
3. Resuelve la petición en milisegundos si detecta un *Cache Hit* (superando el umbral de confianza predefinido), evitando la llamada a la API del proveedor LLM y eliminando el coste de inferencia.

## Arquitectura

El ecosistema está contenerizado e implementa un diseño *stateless* en la capa de aplicación, delegando el estado a la base de datos en memoria para permitir el escalado horizontal.

```mermaid
graph TD
    Client[Cliente / Streamlit UI] -->|POST /chat| API[FastAPI Router]
    
    subgraph Capa de Aplicación stateless
        API --> Vectorizer[Motor de Embeddings local<br>all-MiniLM-L6-v2]
    end
    
    subgraph Capa de Datos Persistente
        Vectorizer -->|Vector FLOAT32| Redis[(Redis Stack<br>Index: Flat L2/Cosine)]
    end
    
    Redis -->|Similitud >= 0.92| Hit[Cache Hit]
    Redis -->|Similitud < 0.92| Miss[Cache Miss]
    
    Hit -->|Retorno O 10ms| Client
    
    Miss -->|Llamada API externa| LLM[LLM Comercial<br>GPT-4 / Claude 3]
    LLM -->|Escritura asíncrona| Redis
    LLM -->|Retorno O 1500ms| Client
