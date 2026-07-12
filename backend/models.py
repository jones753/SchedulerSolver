from typing import Any, List

from pydantic import BaseModel, Field, model_validator


class Task(BaseModel):
    id: str
    name: str
    quantity: int = Field(gt=0)
    time_per_item: int = Field(gt=0)
    machine: str | None = None
    possible_machines: List[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=5)
    dependencies: List[str] = Field(default_factory=list)
    duration: int | None = None

    @model_validator(mode="before")
    @classmethod
    def populate_duration(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Populate duration if missing
            if data.get("duration") is None:
                quantity = data.get("quantity")
                time_per_item = data.get("time_per_item")
                if quantity is not None and time_per_item is not None:
                    data["duration"] = int(quantity) * int(time_per_item)

            # If `machine` not provided, fall back to the first possible_machine
            if not data.get("machine"):
                pm = data.get("possible_machines") or []
                if pm:
                    data["machine"] = pm[0]
        return data


class OptimizationRequest(BaseModel):
    tasks: List[Task]


class OptimizationResponse(BaseModel):
    message: str
    makespan: int
    tasks: List[dict[str, Any]]
    optimized_schedule: List[dict[str, Any]]
