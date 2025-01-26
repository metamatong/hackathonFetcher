from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
import logging
from fastapi.responses import JSONResponse

from . import crawler
from . import schemas

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI()
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Vercel!"}

@app.get("/hackathons", response_model=schemas.HackathonResponse)
def get_hackathons():
    DEVPOST_API_BASE = "https://devpost.com/api/hackathons"
    url = f"{DEVPOST_API_BASE}?order_by=recently-added&status[]=upcoming&page=1"

    logger.info(f"Fetching hackathons from URL: {url}")

    hackathons = crawler.fetch_hackathon_data(url)

    if not hackathons:
        logger.warning("No hackathons found or unable to fetch data.")
        raise HTTPException(status_code=404, detail="No hackathons found or unable to fetch data.")

    logger.info(f"Fetched {len(hackathons)} hackathons successfully.")
    return {"hackathons": hackathons}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )