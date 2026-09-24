from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Support Assistant API")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        return AskResponse(answer="Please provide a question.")

    answer = f"You asked: {question}"
    return AskResponse(answer=answer)
