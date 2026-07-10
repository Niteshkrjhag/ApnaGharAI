from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import CalculationRequest, CalculationResponse, AgentDebateResult, MathEngineResult
from agents import run_multi_agent_debate
from math_engine import run_math_engine
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ApnaGharAI Backend")

# Allow CORS for local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FinalCalculationPayload(BaseModel):
    request: CalculationRequest
    debate: AgentDebateResult

@app.post("/api/analyze", response_model=AgentDebateResult)
async def analyze_risks(request: CalculationRequest):
    try:
        # Phase 1: 3 Parallel AI Agents debate and fetch real-world data
        return await run_multi_agent_debate(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calculate_final", response_model=MathEngineResult)
async def calculate_final(payload: FinalCalculationPayload):
    try:
        # Phase 2: Rigid Math Engine applies the formulas based on potentially user-edited assumptions
        return run_math_engine(payload.request, payload.debate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
