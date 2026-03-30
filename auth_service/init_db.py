import asyncio
from database import users_collection
from security import get_password_hash

# veritabanında hiç kullanıcı yoksa, varsayılan admin kullanıcısını oluşturur
async def create_initial_admin():
    user_count = await users_collection.count_documents({})
    if user_count == 0:
        admin_user = {
            "username": "admin",
            # "1234" olan şifre hash'lenerek kaydedilir
            "hashed_password": get_password_hash("1234"),
            "role": "admin"
        }
        await users_collection.insert_one(admin_user)
        print("Sisteme varsayılan admin kullanıcısı başarıyla eklendi!")
    else:
        print("Veritabanında halihazırda kullanıcılar mevcut. Başlangıç işlemi atlandı.")