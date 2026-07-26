from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.core import Account
from app.schemas import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead, status_code=201)
def create_account(payload: AccountCreate, session: Session = Depends(get_session)) -> Account:
    obj = Account(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[AccountRead])
def list_accounts(
    include_archived: bool = False, session: Session = Depends(get_session)
) -> list[Account]:
    q = select(Account)
    if not include_archived:
        q = q.where(Account.archived == False)  # noqa: E712
    return list(session.exec(q.order_by(Account.sort_order, Account.id)).all())


@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, session: Session = Depends(get_session)) -> Account:
    obj = session.get(Account, account_id)
    if not obj:
        raise HTTPException(404, "account not found")
    return obj


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int, payload: AccountUpdate, session: Session = Depends(get_session)
) -> Account:
    obj = session.get(Account, account_id)
    if not obj:
        raise HTTPException(404, "account not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Account, account_id)
    if not obj:
        raise HTTPException(404, "account not found")
    session.delete(obj)
    session.commit()
