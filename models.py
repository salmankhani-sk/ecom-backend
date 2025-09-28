# models.py
from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy import ForeignKey, Integer, String, Numeric, Boolean, text
from database import Base  # importing the Base we defined

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, server_default=text("0.00"))
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category: Mapped["Category"] = relationship("Category", back_populates="products")
