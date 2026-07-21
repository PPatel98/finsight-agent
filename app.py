import streamlit as st
import requests

st.set_page_config(
    page_title="FinSight Agent",
    page_icon="$",
    layout="centered"
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("FinSight Agent")
st.markdown(
    "Ask anything about a company — current price, "
    "recent news, or insights from their SEC filings."
)
st.divider()

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_question = st.chat_input("Ask about any company...")

if user_question:
    with st.chat_message("user"):
        st.markdown(user_question)
    
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question
    })
    
    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            try:
                response = requests.post(
                    "http://localhost:8000/research",
                    json={
                        "question": user_question,
                        "chat_history": st.session_state.chat_history
                    },
                    timeout=120
                )
                answer = response.json()["result"]
            
            except requests.exceptions.ConnectionError:
                answer = "Cannot connect to the research agent. Make sure the API server is running."
            
            except Exception as e:
                answer = f"Something went wrong: {str(e)}"
        
        st.markdown(answer)
    
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer
    })