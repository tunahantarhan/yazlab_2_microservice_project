from pydantic import BaseModel
from typing import Optional

# kullanıcı sign up/sign in sırasında kullanılacak şema
class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

# veritabanına kaydederken password'u şifrelenmiş bir şekilde tutma şeması
class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role: str
