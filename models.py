from pydantic import BaseModel
from typing import List

class State(BaseModel):
    email: str
    step_count: int = 0

class MyAction(BaseModel):
    action_type: str  # reply / archive / spam / flag

class MyObservation(BaseModel):
    email: str
    reward: float
    done: bool
    info: dict = {}