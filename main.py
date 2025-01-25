from fastapi import FastAPI, HTTPException
import crawler
import schemas

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "Welcome to Vercel!"}

@app.get("/hackathons", response_model=schemas.HackathonResponse)
def get_hackathons():
    DEVPOST_API_BASE = "https://devpost.com/api/hackathons"
    url = f"{DEVPOST_API_BASE}?order_by=recently-added&status[]=upcoming&page=1"

    hackathons = crawler.fetch_hackathon_data(url)

    if not hackathons:
        raise HTTPException(status_code=404, detail="No hackathons found or unable to fetch data.")

    return {"hackathons": hackathons}