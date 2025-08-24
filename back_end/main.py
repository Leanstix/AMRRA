from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from agents.routers.retriver_route import retriever_router
from agents.routers.extractor_route import extractor_router
from agents.routers.pipeline import router as pipeline_router
from agents.routers.experimentation_router import experimentation_router
from agents.routers.judging_router import judging_router

load_dotenv()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retriever_router)
app.include_router(extractor_router)
app.include_router(pipeline_router)
app.include_router(experimentation_router)
app.include_router(judging_router)


@app.get("/")
def read_root():
    return {"message": "Back end for the Automated Machine learning Research Reproducibility Assistant!"}

