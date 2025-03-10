from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.api.deps import check_librarian_access, get_current_active_user
from app.schemas.book import (
    BookCreate, BookUpdate, Book, CategoryCreate,
    PaginatedCategoryResponse, Category, BookSearchParams, PaginatedBookResponse, BookItemCreate, BookItem
)
from app.services import books as book_service

router = APIRouter()


@router.post("/categories", response_model=Category)
def create_category(
    category: CategoryCreate,
    _: Dict[str, Any] = Depends(check_librarian_access)
):
    return book_service.create_category(category)


@router.get("/categories", response_model=PaginatedCategoryResponse)
def get_categories(
    page: int = 0,
    limit: int = 100,
    _: Dict[str, Any] = Depends(get_current_active_user)
):
    return book_service.get_categories(page, limit)


@router.post("", response_model=Book)
def create_book(
    book: BookCreate,
    _: Dict[str, Any] = Depends(check_librarian_access)
):
    return book_service.create_book(book)


@router.post("/copy", response_model=Book)
def add_book_copy(
    book_copy: BookItemCreate,
    _: Dict[str, Any] = Depends(check_librarian_access)
):
    return book_service.add_book_copy(book_copy)


@router.get("", response_model=PaginatedBookResponse)
def search_books(
    params: BookSearchParams = Depends(),
    _: Dict[str, Any] = Depends(get_current_active_user)
):
    return book_service.search_books(params)


@router.get("/{book_id}", response_model=Book)
def get_book(
    book_id: int,
    _: Dict[str, Any] = Depends(get_current_active_user)
):
    return book_service.get_book(book_id)


@router.put("/{book_id}", response_model=Book)
def update_book(
    book_id: int,
    book_update: BookUpdate,
    _: Dict[str, Any] = Depends(check_librarian_access)
):
    return book_service.update_book(book_id, book_update)


@router.delete("/{book_id}", response_model=Dict[str, str])
def delete_book(
    book_id: int,
    _: Dict[str, Any] = Depends(check_librarian_access)
):
    return book_service.delete_book(book_id)
