# app/schemas.py

from pydantic import BaseModel
from typing import List

class Hackathon(BaseModel):
    name: str
    url: str
    location: str
    prize: str
    date: str

class HackathonResponse(BaseModel):
    hackathons: List[Hackathon]