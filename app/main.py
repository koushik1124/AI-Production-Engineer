from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.health import router as health_router
from app.api.incidents import router as incidents_router
from app.api.simulator import router as simulator_router
from app.database.database import Base, engine
from app.llm.groq import GroqLLM
from app.models.incident_db import IncidentDB
from app.policy.engine import PolicyEngine


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Production Engineer",
    description="AI-powered incident investigation and response platform",
    version="0.1.0",
)


# Allow the React frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(health_router)
app.include_router(incidents_router)
app.include_router(simulator_router)


# Initialize LLM instance once
llm = GroqLLM()


class PromptRequest(BaseModel):
    prompt: str


@app.get("/")
async def root():
    return {
        "name": "AI Production Engineer",
        "version": "0.1.0",
        "status": "running",
    }


@app.post("/ai/test")
async def test_ai(request: PromptRequest):
    response = await llm.generate(request.prompt)

    return {
        "response": response
    }


@app.get("/policy/test/{action}")
async def test_policy(action: str):
    engine = PolicyEngine()

    decision = engine.evaluate(action)

    return decision.model_dump()