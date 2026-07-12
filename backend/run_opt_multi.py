import json
from types import SimpleNamespace
from pprint import pprint

#from .optimizer import optimize_tasks
from optimizer import optimize_tasks


def load_tasks(path: str):
    with open(path, "r") as f:
        data = json.load(f)
    tasks = []
    for d in data:
        # Ensure compatibility: set `machine` to first possible if not provided
        if "machine" not in d or d.get("machine") is None:
            pm = d.get("possible_machines")
            if pm:
                d["machine"] = pm[0]
        tasks.append(SimpleNamespace(**d))
    return tasks


if __name__ == "__main__":
    tasks = load_tasks("backend/sample_tasks_multi_machine.json")
    result = optimize_tasks(tasks)
    pprint(result)