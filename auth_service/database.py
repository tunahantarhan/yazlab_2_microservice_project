import os
from motor.motor_asyncio import AsyncIOMotorClient

# auth db, docker-compose'da ayarladığımız standart port olan 27017 üzerinde
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_URL)

db = client.auth_db
users_collection = db.get_collection("users")