from typing import List
from pydantic import BaseModel

class Hackathon(BaseModel):
    name: str
    url: str
    location: str
    prize: str
    date: str

class HackathonResponse(BaseModel):
    hackathons: List[Hackathon]