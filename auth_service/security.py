import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt

# şifreleme algoritması (bcrypt) ayarları
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# token oluşturma (jwt) ayarları
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "gizli-auth-anahtari")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # token yarım saat geçerli olur

# ---- ŞİFRELEME FONKSİYONLARI ----

# kullanıcı şifresi ile db'deki enkript edilmiş şifreyi karşılaştırır
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# düz metin halindeki şifreyi bcrypt ile enkript eder
def get_password_hash(password):
    return pwd_context.hash(password)

# --- TOKENİZASYON FONKSİYONLARI ---

# kullanıcı bilgileriyle imzalı bir jwt (token) oluşturur
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # token "secret key" ile imzalanır
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# gelen token'ın süresini ve geçerliliğini kontrol eder
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  
    except jwt.InvalidTokenError:
        return None
