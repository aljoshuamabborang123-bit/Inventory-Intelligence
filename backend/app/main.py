
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Part
from app.schemas import PartCreate, PartResponse, PartUpdate


app = FastAPI(title="Inventory Intelligence API", version="0.1.0")


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/parts", response_model=list[PartResponse], tags=["Parts"])
def get_parts(
    category: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[PartResponse]:

    statement = select(Part)

    if category:
        statement = statement.where(
            func.lower(Part.category) == category.lower()
        )

    statement = statement.limit(limit)

    return list(db.scalars(statement).all())


@app.post(
    "/parts",
    response_model=PartResponse,
    status_code=201,
    tags=["Parts"],
)
def create_part(
    part: PartCreate,
    db: Session = Depends(get_db),
) -> PartResponse:

    new_part = Part(**part.model_dump())

    db.add(new_part)
    db.commit()
    db.refresh(new_part)

    return new_part


@app.get(
    "/parts/{part_id}",
    response_model=PartResponse,
    tags=["Parts"],
)
def get_part(
    part_id: int,
    db: Session = Depends(get_db),
) -> PartResponse:

    part = db.get(Part, part_id)

    if part is None:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    return part


@app.put(
    "/parts/{part_id}",
    response_model=PartResponse,
    tags=["Parts"],
)
def update_part(
    part_id: int,
    part: PartUpdate,
    db: Session = Depends(get_db),
) -> PartResponse:

    existing_part = db.get(Part, part_id)

    if existing_part is None:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    for field, value in part.model_dump().items():
        setattr(existing_part, field, value)

    db.commit()
    db.refresh(existing_part)

    return existing_part


@app.delete(
    "/parts/{part_id}",
    status_code=204,
    tags=["Parts"],
)
def delete_part(
    part_id: int,
    db: Session = Depends(get_db),
) -> None:

    part = db.get(Part, part_id)

    if part is None:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    db.delete(part)
    db.commit()
