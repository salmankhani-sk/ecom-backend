# main.py
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Generator
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
import models  # make sure models are imported so tables are known

app = FastAPI(title="class-e-commerce-backend")

# create tables at startup (simple for Day-1; later we'll teach Alembic)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# DB session per request
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request/Response shapes (Pydantic)
class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool = True

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool
    class Config:
        from_attributes = True

# tiny endpoints
@app.get("/health")
def health():
    return {"status": "ok", "app": "class-e-commerce-backend"}

@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    item = models.Product(name=payload.name, price=payload.price, in_stock=payload.in_stock)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.id.desc()).all()
