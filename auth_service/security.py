import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt

# şifreleme algoritması (bcrypt) ayarları
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# token oluşturma (jwt) ayarları
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "gizli-auth-anahtari")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # token yarım saat geçerli olacak

# ---- şifreleme fonksiyonları ----

# kullanıcı şifresi ile db'deki enkript edilmiş şifreyi karşılaştırır
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# düz metin halindeki şifreyi bcrypt ile enkript eder
def get_password_hash(password):
    return pwd_context.hash(password)