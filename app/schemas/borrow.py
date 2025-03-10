from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class BorrowRequest(BaseModel):
    book_id: int
    due_date: datetime


class Borrow(BaseModel):
    id: int
    user_id: int
    book_item_id: int
    borrowed_date: datetime
    due_date: datetime
    returned_date: Optional[datetime] = None
    status: str
    is_overdue: bool
    days_remaining: Optional[int] = None
    days_overdue: Optional[int] = None
    book_details: dict


class PaginatedBorrowResponse(BaseModel):
    borrows: List[Borrow]
    page: int
    size: int
    total: int
    number_of_pages: int


class ReturnRequest(BaseModel):
    borrow_id: int


class BorrowHistoryParams(BaseModel):
    user_id: Optional[int] = None
    status: Optional[str] = None
    is_overdue: Optional[bool] = None
    page: int = 0
    limit: int = 10
