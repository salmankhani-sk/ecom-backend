# models.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Numeric, Boolean, text
from database import Base  # importing the Base we defined

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, server_default=text("0.00"))
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
