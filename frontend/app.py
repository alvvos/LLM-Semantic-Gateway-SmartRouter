import streamlit as st
import requests
import os

st.set_page_config(page_title="Semantic gateway", layout="wide")

api_url = os.getenv("API_URL", "http://localhost:8000/chat")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "metrics" not in st.session_state:
    st.session_state.metrics = {
        "total_requests": 0,
        "cache_hits": 0,
        "total_latency": 0.0,
        "cost_saved_usd": 0.0
    }

st.title("Semantic gateway: finops & llmops")
st.markdown("Demostración de interceptación de prompts con caché semántica en redis.")

with st.sidebar:
    st.header("Dashboard de negocio")
    st.markdown("Métricas acumuladas de esta sesión:")
    
    m = st.session_state.metrics
    hit_rate = (m["cache_hits"] / m["total_requests"] * 100) if m["total_requests"] > 0 else 0
    avg_latency = (m["total_latency"] / m["total_requests"]) if m["total_requests"] > 0 else 0
    
    st.metric("Peticiones totales", m["total_requests"])
    st.metric("Tasa de acierto", f"{hit_rate:.1f}%")
    st.metric("Latencia media", f"{avg_latency:.3f} s")
    st.metric("Ahorro estimado", f"${m['cost_saved_usd']:.4f}")
    
    if st.button("Limpiar historial"):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg:
            st.caption(msg["meta"])

if prompt := st.chat_input("Escribe tu consulta:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("procesando..."):
        try:
            response = requests.post(api_url, json={"prompt": prompt})
            data = response.json()
            
            answer = data["response"]
            status = data["status"].lower()
            latency = data["latency_sec"]
            is_hit = data["cost_saved"]
            score = data.get("similarity_score")
            if score is None:
                score = "n/a"
            
            st.session_state.metrics["total_requests"] += 1
            st.session_state.metrics["total_latency"] += latency
            if is_hit:
                st.session_state.metrics["cache_hits"] += 1
                st.session_state.metrics["cost_saved_usd"] += 0.01
                
            meta_text = f"status: {status} | latencia: {latency}s"
            if score != "n/a":
                meta_text += f" | similitud: {score}"

            st.session_state.messages.append({"role": "assistant", "content": answer, "meta": meta_text})
            
            with st.chat_message("assistant"):
                st.markdown(answer)
                st.caption(meta_text)
                
            st.rerun()
            
        except Exception as e:
            st.error(f"Error conectando a la api: {e}")