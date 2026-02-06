"""
Example Target API for testing the OpenAPI Test Generator.

This is a simple FastAPI application with basic CRUD operations
that serves as the target for generated tests.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(
    title="Example Items API",
    description="A simple API for managing items - used as a test target",
    version="1.0.0",
)

# In-memory storage
items_db: dict[str, dict] = {}


class ItemCreate(BaseModel):
    """Request body for creating an item"""

    name: str
    price: float
    description: Optional[str] = None


class Item(BaseModel):
    """Item response model"""

    id: str
    name: str
    price: float
    description: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """Check if the API is running"""
    return {"status": "ok"}


@app.post(
    "/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"]
)
def create_item(item: ItemCreate):
    """Create a new item"""
    item_id = str(uuid.uuid4())
    new_item = {
        "id": item_id,
        "name": item.name,
        "price": item.price,
        "description": item.description,
    }
    items_db[item_id] = new_item
    return new_item


@app.get("/items", response_model=list[Item], tags=["items"])
def list_items():
    """Get all items"""
    return list(items_db.values())


@app.get("/items/{item_id}", response_model=Item, tags=["items"])
def get_item(item_id: str):
    """Get a specific item by ID"""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{item_id}' not found",
        )
    return items_db[item_id]


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["items"])
def delete_item(item_id: str):
    """Delete an item by ID"""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{item_id}' not found",
        )
    del items_db[item_id]
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
