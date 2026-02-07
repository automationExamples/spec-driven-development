from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import router

app = FastAPI(title="Spec-Driven Task Manager", version="0.1")
app.include_router(router)

# Serve the frontend folder at the app root (index.html will be served)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

app = FastAPI(title="Task API")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
