import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Agents.routers.retriver_route import retriever_router
from Agents.routers.extractor_route import extractor_router
from Agents.Pipeline.pipeline import router as pipeline_router


app = FastAPI(title="Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(retriever_router)
app.include_router(extractor_router)
app.include_router(pipeline_router)


@app.get("/")
def root():
    return {"message": "Multi-Agent API running. Endpoints: /retriever, /extractor, /pipeline, /judge"}
