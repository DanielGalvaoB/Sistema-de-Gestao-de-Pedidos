from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1)
]
Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
PositiveMoney = Annotated[
    Decimal, Field(gt=0, max_digits=12, decimal_places=2)
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
