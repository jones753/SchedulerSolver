import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import OptimizationRequest, OptimizationResponse, Task
from .optimizer import optimize_tasks

app = FastAPI(title="Production Scheduling API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_TASKS_PATH = BASE_DIR / "sample_tasks.json"


def load_sample_tasks() -> list[dict]:
    with SAMPLE_TASKS_PATH.open("r", encoding="utf-8") as handle:
        raw_tasks = json.load(handle)

    enriched_tasks = []
    for raw_task in raw_tasks:
        task_with_duration = dict(raw_task)
        task_with_duration["duration"] = (
            task_with_duration["quantity"] * task_with_duration["time_per_item"]
        )
        enriched_tasks.append(task_with_duration)

    return enriched_tasks


@app.get("/tasks", response_model=list[Task])
def get_tasks() -> list[dict]:
    return load_sample_tasks()


@app.post("/optimize", response_model=OptimizationResponse)
def optimize(request: OptimizationRequest) -> dict:
    return optimize_tasks(request.tasks)
