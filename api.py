from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

app = FastAPI()

class ResearchRequest(BaseModel):
    question: str
    collection_id: str = None
    chat_history: list = None

@app.post("/research")
async def research(request: ResearchRequest):
    result = run_agent(
        user_question = request.question,
        collection_id = request.collection_id,
        chat_history = request.chat_history
    )
    return {"result": result}


