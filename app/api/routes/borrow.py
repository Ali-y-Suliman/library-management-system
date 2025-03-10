from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.schemas.borrow import BorrowRequest, Borrow, ReturnRequest, BorrowHistoryParams, PaginatedBorrowResponse
from app.services import borrow as borrow_service

router = APIRouter()


@router.post("", response_model=Borrow)
def borrow_book(
    borrow_data: BorrowRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    return borrow_service.borrow_book(borrow_data, current_user)


@router.post("/return", response_model=Borrow)
def return_book(
    return_data: ReturnRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    return borrow_service.return_book(current_user, return_data)


@router.get("/history", response_model=PaginatedBorrowResponse)
def get_borrow_history(
    params: BorrowHistoryParams = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    return borrow_service.get_borrow_history(current_user, params)


@router.post("/notify", response_model=Dict[str, str])
def notify_when_available(
    book_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    return borrow_service.notify_when_available(book_id, current_user)
