import pydantic as _pydantic
import datetime as _dt


class _AnalyticBase(_pydantic.BaseModel):
    Nickname: str
    telegram_id: int
    description: str


class AnalyticCreate(_AnalyticBase):
    pass


class Analytic(_AnalyticBase):
    #Read Analytic
    predicts_total: int
    rating: float
    created_date: _dt.datetime
    updated_date = _dt.datetime
    is_active: bool
    bonus: int
    bonuscount: int

    class Config:
        orm_mode = True


class AnalyticPublic(_AnalyticBase):
    predicts_total: int
    rating: float
    is_active: bool

    class Config:
        orm_mode = True