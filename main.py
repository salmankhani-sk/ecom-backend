
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Generator, Optional
from sqlalchemy.orm import Session
import hashlib

from database import Base, engine, SessionLocal
import models  # registering models so create_all can see them

app = FastAPI(title="class-e-commerce-backend")

# ---------- startup: create any missing tables ----------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# ---------- DB session per request ----------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- simple hashing helpers (demo only!) ----------
PEPPER = "class-demo-not-secure"

def hash_password(raw: str) -> str:
    return hashlib.sha256((raw + PEPPER).encode("utf-8")).hexdigest()

def verify_password(raw: str, hashed: str) -> bool:
    return hash_password(raw) == hashed

# ---------- health ----------
@app.get("/health")
def health():
    return {"status": "ok", "app": "class-e-commerce-backend"}


# 
class CategoryCreate(BaseModel):
    name: str

class CategoryOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True



class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool = True
    category_id: Optional[int] = None 

class ProductUpdate(BaseModel):
    name: str
    price: float
    in_stock: bool
    category_id: Optional[int] = None  

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool
    category_id: Optional[int] = None
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user"  # "user" or "admin"

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    class Config:
        from_attributes = True

class LoginInput(BaseModel):
    email: str
    password: str


def admin_required(
    db: Session = Depends(get_db),
    x_admin_email: Optional[str] = Header(default=None, alias="X-Admin-Email")
):
    """
    Classroom-simple guard:
    - Client sends header: X-Admin-Email: admin@demo.com
    - We check DB that this email exists with role='admin'
    """
    if not x_admin_email:
        raise HTTPException(status_code=401, detail="Missing X-Admin-Email header")

    admin = db.query(models.User).filter(
        models.User.email == x_admin_email,
        models.User.role == "admin"
    ).first()

    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin


@app.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    # simple uniqueness check
    exists = db.query(models.Category).filter(models.Category.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Category name already exists")

    cat = models.Category(name=payload.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@app.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name.asc()).all()

@app.get("/categories/{category_id}/products", response_model=List[ProductOut])
def list_products_by_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    return (
        db.query(models.Product)
        .filter(models.Product.category_id == category_id)
        .order_by(models.Product.id.desc())
        .all()
    )



@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    # If a category is supplied, ensure it exists
    if payload.category_id is not None:
        cat = db.query(models.Category).filter(models.Category.id == payload.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    item = models.Product(
        name=payload.name,
        price=payload.price,
        in_stock=payload.in_stock,
        category_id=payload.category_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.id.desc()).all()

@app.get("/products/{product_id}", response_model=ProductOut)
def read_product(product_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item

@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")

    # validate category if provided
    if payload.category_id is not None:
        cat = db.query(models.Category).filter(models.Category.id == payload.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    item.name = payload.name
    item.price = payload.price
    item.in_stock = payload.in_stock
    item.category_id = payload.category_id

    db.commit()
    db.refresh(item)
    return item

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(item)
    db.commit()
    # 204 No Content
    return



@app.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # check unique email
    exists = db.query(models.User).filter(models.User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role if payload.role in ("user", "admin") else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.id.desc()).all()

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u

@app.post("/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    u = db.query(models.User).filter(models.User.email == data.email).first()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "login ok", "role": u.role}

@app.get("/admin/users", response_model=List[UserOut])
def admin_list_users(
    db: Session = Depends(get_db),
    _admin = Depends(admin_required),
):
    return db.query(models.User).order_by(models.User.id.desc()).all()