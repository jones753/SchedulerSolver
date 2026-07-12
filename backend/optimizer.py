from typing import Any

from ortools.sat.python import cp_model

#from .models import Task
from models import Task


def optimize_tasks(tasks: list[Task]) -> dict[str, Any]:
    """
    Schedule tasks on available machines with CP-SAT and return start/finish times.
    """
    if not tasks:
        return {
            "message": "No tasks were provided.",
            "makespan": 0,
            "tasks": [],
            "optimized_schedule": [],
        }

    # Collect the set of all machines mentioned by tasks. Tasks may provide
    # `possible_machines` (list) or a single `machine` (str).
    machine_set = set()
    for task in tasks:
        pm = getattr(task, "possible_machines", None)
        if pm:
            for m in pm:
                machine_set.add(m)
        else:
            machine_set.add(task.machine)
    machines = sorted(machine_set)

    processing_times = {}
    for task in tasks:
        processing_times[task.id] = task.quantity * task.time_per_item

    horizon = sum(processing_times.values()) # max possible time for all tasks to complete if done sequentially

    model = cp_model.CpModel()

    # Create one optional interval per task-machine pair.
    task_vars: dict[str, dict[str, Any]] = {}

    # loop through each task to create variables and constraints
    for task in tasks:
        task_id = task.id
        task_vars[task_id] = {
            "task_start": model.NewIntVar(0, horizon, f"{task_id}_start"),
            "task_end": model.NewIntVar(0, horizon, f"{task_id}_end"),
            "machine_start": {},
            "machine_end": {},
            "machine_assignment": {},
            "machine_interval": {},
        }

        for machine in machines:
            # task’s start and end variables for each machine
            start_var = model.NewIntVar(0, horizon, f"{task_id}_{machine}_start")
            end_var = model.NewIntVar(0, horizon, f"{task_id}_{machine}_end")
            assignment_var = model.NewBoolVar(f"{task_id}_{machine}_assign")

            interval = model.NewOptionalIntervalVar(
                start_var,
                processing_times[task_id],
                end_var,
                assignment_var,
                f"{task_id}_{machine}_interval",
            )

            task_vars[task_id]["machine_start"][machine] = start_var
            task_vars[task_id]["machine_end"][machine] = end_var
            task_vars[task_id]["machine_assignment"][machine] = assignment_var
            task_vars[task_id]["machine_interval"][machine] = interval

        # By this point, all task/machine variables exist; now we add the scheduling constraints that tie them together

        # Each task must be assigned to exactly one machine.
        machine_options = []
        for machine in machines:
            machine_options.append(task_vars[task_id]["machine_assignment"][machine])
        model.Add(sum(machine_options) == 1)

        # Restrict assignments to the task's allowed machines only. If a task
        # provides `possible_machines` it may run on any of those; otherwise
        # fall back to the single `machine` attribute.
        allowed_machines = getattr(task, "possible_machines", None)
        if not allowed_machines:
            allowed_machines = [task.machine]
        for machine in machines:
            if machine not in allowed_machines:
                model.Add(task_vars[task_id]["machine_assignment"][machine] == 0)

        # Link task-level start/end to the chosen machine's start/end
        for machine in machines:
            model.Add(task_vars[task_id]["task_start"] == task_vars[task_id]["machine_start"][machine]).OnlyEnforceIf(
                task_vars[task_id]["machine_assignment"][machine]
            )
            model.Add(task_vars[task_id]["task_end"] == task_vars[task_id]["machine_end"][machine]).OnlyEnforceIf(
                task_vars[task_id]["machine_assignment"][machine]
            )

    # Prevent overlapping work on the same machine.
    for machine in machines:
        machine_intervals = []
        for task in tasks:
            machine_intervals.append(task_vars[task.id]["machine_interval"][machine])
        model.AddNoOverlap(machine_intervals)

    # Minimize overall completion time (makespan).
    makespan = model.NewIntVar(0, horizon, "makespan")
    for task in tasks:
        task_id = task.id
        # makespan must be at least the end time for whichever machine the task is assigned to
        for machine in machines:
            model.Add(makespan >= task_vars[task_id]["machine_end"][machine]).OnlyEnforceIf(
                task_vars[task_id]["machine_assignment"][machine]
            )

    # Precedence constraints: enforce task dependencies if provided
    id_to_task = {}
    for t in tasks:
        id_to_task[t.id] = t
    for task in tasks:
        if not getattr(task, "dependencies", None):
            continue
        for dep_id in task.dependencies:
            if dep_id not in id_to_task:
                # skip unknown dependencies
                continue
            # task cannot start before dependency finishes
            model.Add(task_vars[task.id]["task_start"] >= task_vars[dep_id]["task_end"])

    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "message": "The solver could not find a valid schedule.",
            "makespan": 0,
            "tasks": [],
            "optimized_schedule": [],
        }

    optimized_tasks: list[dict[str, Any]] = []
    optimized_schedule: list[dict[str, Any]] = []

    for task in tasks:
        task_id = task.id
        assigned_machine = next(
            machine
            for machine in machines
            if solver.Value(task_vars[task_id]["machine_assignment"][machine])
        )
        start_time = solver.Value(task_vars[task_id]["machine_start"][assigned_machine])
        finish_time = solver.Value(task_vars[task_id]["machine_end"][assigned_machine])

        optimized_tasks.append(
            {
                "id": task.id,
                "name": task.name,
                "quantity": task.quantity,
                "time_per_item": task.time_per_item,
                "machine": assigned_machine,
                "priority": task.priority,
                "duration": processing_times[task_id],
                "start_time": start_time,
                "finish_time": finish_time,
            }
        )

        optimized_schedule.append(
            {
                "id": task.id,
                "name": task.name,
                "machine": assigned_machine,
                "start_time": start_time,
                "finish_time": finish_time,
            }
        )

    return {
        "message": "Optimization completed successfully.",
        "makespan": solver.Value(makespan),
        "tasks": optimized_tasks,
        "optimized_schedule": optimized_schedule,
    }
