import json
import os
from pathlib import Path

MEMORY_STATE = Path("app_state.json")

def clear_state():
    if MEMORY_STATE.exists():
        try:
            os.remove(MEMORY_STATE)
            print(f"State file {MEMORY_STATE} has been removed.")
        except Exception as e:
            print(f"Error removing state file: {e}")
        
def load_state():
    if MEMORY_STATE.exists():
        with open(MEMORY_STATE, "r") as f:
            return json.load(f)
    return {"iterations": []}

def save_state(state: dict):
    with open(MEMORY_STATE, "w") as f:
        json.dump(state, f, indent=2)

def log_iteration(response):
    state = load_state()
    current_step = len(state["iterations"]) + 1

    iteration = {
        "iteration": current_step,
        "response": response
    }

    state["iterations"].append(iteration)
    save_state(state)
    return state
