import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="Clothing Brand API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Clothing Brand API running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# Request model for creating a product
class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str  # Minimal, Anime, Christian
    in_stock: bool = True
    image_url: Optional[str] = None
    tags: Optional[List[str]] = []

@app.post("/api/products")
def create_product(product: ProductCreate):
    try:
        # Validate against Pydantic Product schema for collection definition
        validated = Product(
            title=product.title,
            description=product.description,
            price=product.price,
            category=product.category,
            in_stock=product.in_stock,
            image_url=product.image_url,
            tags=product.tags or []
        )
        inserted_id = create_document("product", validated)
        return {"id": inserted_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/products")
def list_products(category: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {"category": category} if category else {}
        docs = get_documents("product", filter_dict=filter_dict, limit=limit)
        # Convert ObjectId and datetime to strings
        for d in docs:
            d["_id"] = str(d.get("_id"))
            if "created_at" in d:
                d["created_at"] = str(d["created_at"]) 
            if "updated_at" in d:
                d["updated_at"] = str(d["updated_at"]) 
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
