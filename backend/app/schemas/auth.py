from pydantic import BaseModel


class LoginIn(BaseModel):
    tenant_id: str
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    tenant_id: str
    username: str
    role: str

    model_config = {"from_attributes": True}
