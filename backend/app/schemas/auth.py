from pydantic import BaseModel


class LoginIn(BaseModel):
    tenant_id: str
    username: str
    password: str


class LoginOut(BaseModel):
    user: dict
    tenant_id: str


class UserOut(BaseModel):
    user_id: int
    username: str
    tenant_id: str
    role: str

    model_config = {"from_attributes": True}
