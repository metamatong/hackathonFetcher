# Hackathon Fetcher API

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95.2-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)


## 📖 Introduction

Welcome to the **Hackathon Crawler API**! This project is a web crawler built with FastAPI and Python's `Requests` library. It fetches hackathon information from Devpost's API, filters the data based on specific criteria, and serves the information through a RESTful API. Whether you're looking to discover upcoming hackathons in British Columbia, Vancouver, or online, this API provides a streamlined and efficient solution.

## ✨ Features

- **API-Based Crawling**: Utilizes Devpost's API to fetch hackathon data efficiently.
- **Advanced Filtering**: 
  - **Status**: Retrieves only upcoming and recently added hackathons.
  - **Location**: Filters hackathons located in Vancouver, British Columbia (BC), or online.
  - **Prize Currency**: Includes hackathons awarding prizes in USD or CAD only, excluding others like INR or GBP.
- **Caching Mechanism**: Implements Redis provided by UpStash to avoid redundant API calls and improve performance.
- **Geocoding Verification**: Uses Google Maps API to confirm hackathon locations within British Columbia.
- **Environment Configuration**: Manages sensitive information like API keys using environment variables.
- **Error Handling**: Robust error management to handle API request failures and data parsing issues gracefully.
- **API Documentation**: Interactive Swagger UI and ReDoc documentation generated automatically by FastAPI.
- **Extensible**: Easily extendable to support additional filters or data sources.

## 🛠️ Tech Stack

- **Programming Language**: Python 3.8+
- **Web Framework**: FastAPI
- **HTTP Requests**: Requests
- **Caching**: Custom in-memory caching
- **Environment Management**: python-dotenv
- **Server**: Uvicorn
- **Others**: Pydantic for data validation, Logging for monitoring
