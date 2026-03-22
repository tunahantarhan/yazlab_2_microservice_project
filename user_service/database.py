from motor.motor_asyncio import AsyncIOMotorClient

# user_db, izolasyon sağlanması ve veritabanı çakışması olmaması adına 27018 portunda.
MONGO_URL = "mongodb://user_db:27017"

client = AsyncIOMotorClient(MONGO_URL)
database = client.user_db
user_collection = database.get_collection("users")