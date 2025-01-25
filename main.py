from fastapi import FastAPI, HTTPException

import crawler
import schemas
from routers import items

app = FastAPI(
    title="Hackathon Crawler API",
    description="An API to fetch and serve hackathon information.",
    version="1.0.0"
)


@app.get("/", tags=["Home"])
def read_root():
    return {"message": "Welcome to the Hackathon Crawler API!"}

@app.get("/hackathons", response_model=schemas.HackathonResponse, tags=["Hackathons"])
def get_hackathons():
    """
    Fetch hackathon data from the provided URL.
    """

    DEVPOST_API_BASE = "https://devpost.com/api/hackathons"
    url = f"{DEVPOST_API_BASE}?order_by=recently-added&status[]=upcoming&page=1"

    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required.")

    hackathons = crawler.fetch_hackathon_data(url)

    if not hackathons:
        raise HTTPException(status_code=404, detail="No hackathons found or unable to fetch data.")

    return {"hackathons": hackathons}

app.include_router(items.router)
