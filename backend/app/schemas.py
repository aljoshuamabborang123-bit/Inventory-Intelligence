from pydantic import BaseModel, ConfigDict, Field


class PartCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)


class PartUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)


class PartResponse(BaseModel):
    id: int
    name: str
    category: str
    quantity: int

    model_config = ConfigDict(from_attributes=True)
