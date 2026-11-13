from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Earth Trend Detective API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    variable: str
    location: str
    start_year: int
    end_year: int

@app.get("/")
def home():
    return {"message": "Earth Trend Detective API is running!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/analyze")
def analyze(request: AnalysisRequest):

    # Temporary response to test integration
    return {
        "variable": request.variable,
        "location": request.location,
        "period": f"{request.start_year}-{request.end_year}",
        "trend": {
            "direction": "increasing",
            "slope": 0.035
        },
        "significance": {
            "p_value": 0.012,
            "significant": True
        }
    }






