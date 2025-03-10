from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.db.models import BookStatus


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    book_count: Optional[int] = None


class PaginatedCategoryResponse(BaseModel):
    categories: List[Category]
    page: int
    size: int
    total: int
    number_of_pages: int


class BookItemBase(BaseModel):
    book_id: int
    isbn: str = Field(..., min_length=10, max_length=20)
    location: Optional[str] = None
    status: str = BookStatus.AVAILABLE


class BookItemCreate(BookItemBase):
    pass


class BookItem(BookItemBase):
    id: int
    acquisition_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaginatedBookItemResponse(BaseModel):
    book_items: List[BookItem]
    page: int
    size: int
    total: int
    number_of_pages: int


class BookBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=50)
    author: str = Field(..., min_length=2, max_length=50)
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    total_quantity: int = 1
    available_quantity: int = 1


class BookCreate(BaseModel):
    isbn: str
    location: str
    title: str = Field(..., min_length=2, max_length=50)
    author: str = Field(..., min_length=2, max_length=50)
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    category_ids: List[int] = []


class BookUpdate(BaseModel):
    title: Optional[str] = Field(..., min_length=2, max_length=50)
    author: Optional[str] = Field(..., min_length=2, max_length=50)
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    total_quantity: Optional[int] = None
    available_quantity: Optional[int] = None
    category_ids: Optional[List[int]] = None


class Book(BookBase):
    id: int
    categories: List[Category] = []
    created_at: datetime
    updated_at: datetime


class PaginatedBookResponse(BaseModel):
    books: List[Book]
    page: int
    size: int
    total: int
    number_of_pages: int


class BookSearchParams(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category_id: Optional[int] = None
    publication_year: Optional[int] = None
    available_only: Optional[bool] = False
    page: int = 0
    limit: int = 10
