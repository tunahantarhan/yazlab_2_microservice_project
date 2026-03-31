from pydantic import BaseModel
from typing import Optional

class LoginModel(BaseModel):
    username: str
    password: str