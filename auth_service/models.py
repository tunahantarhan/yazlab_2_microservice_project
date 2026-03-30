from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

# veritabanına kaydederken password'u şifrelenmiş bir şekilde tutma şeması
class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role: str

# token dönerken kullanılacak klasik şema
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str