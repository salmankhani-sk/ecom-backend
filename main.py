# main.py
from fastapi import FastAPI, Depends,HTTPException
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
    category_id: int | None = None

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool
    class Config:
        from_attributes = True
class ProductUpdate(BaseModel):
    name: str
    price: float
    in_stock: bool
class CategoryCreate(BaseModel):
    name: str
class CategoryOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

@app.get("/tu")
def health():
    return {"status": "ok", "app": "class-e-commerce-backend"}
@app.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    exist = db.query(models.Category).filter(models.Category.name==payload.name).first()
    if exist:
        raise HTTPException(status_code=400, detail="Category already exists")
    cat = models.Category(name=payload.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat
@app.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.id.desc()).all()
@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if payload.category_id:
        cat = db.query(models.Category).filter(models.Category.id==payload.category_id).first()
        if not cat:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Category not found")
    item = models.Product(
        name=payload.name,
        price=payload.price,
        in_stock=payload.in_stock,
        category_id=payload.category_id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.id.desc()).all()

@app.get("/categories/{category_id}/products", response_model=List[ProductOut])
def list_products_by_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(models.Category).filter(models.Category.id==category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return db.query(models.Product).filter(models.Product.category_id==category_id).order_by(models.Product.id.desc()).all()
# @app.get("/products/{product_id}", response_model=ProductOut)
# def read_product(product_id: int, db: Session = Depends(get_db)):
#     item = db.get(models.Product, product_id)
#     if not item:
#         return {"status": "not found"}
#     return item
# @app.put("/products/{product_id}",response_model = ProductUpdate)
# def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
#     item = db.get(models.Product, product_id)
#     if not item:
#         return {"status": "not found"}
#     item.name = payload.name
#     item.price = payload.price
#     item.in_stock = payload.in_stock
#     db.commit()
#     db.refresh(item)
#     return item
# @app.delete("/products/{product_id}",status_code=204)
# def delete_product(product_id: int, db: Session = Depends(get_db)):
#     item = db.get(models.Product, product_id)
#     if not item:
#         raise HTTPException(status_code=404, detail="Product not found")
#     db.delete(item)
#     db.commit()
#     return {"status": "deleted"}