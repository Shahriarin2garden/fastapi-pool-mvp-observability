from pydantic import BaseModel, EmailStr, conint, constr


class OrderCreate(BaseModel):
    customer_email: EmailStr
    item: constr(min_length=1, max_length=100)
    quantity: conint(gt=0, le=1000)
    amount_cents: conint(ge=0)


class OrderResponse(OrderCreate):
    id: int
    status: str
