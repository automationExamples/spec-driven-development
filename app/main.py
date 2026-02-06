"""
Main Application - FastAPI entry point for the OpenAPI Test Generator.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router


app = FastAPI(
    title="OpenAPI Test Generator",
    description="Generate and run pytest tests from OpenAPI specifications",
    version="1.0.0",
)

# Add CORS middleware for Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
