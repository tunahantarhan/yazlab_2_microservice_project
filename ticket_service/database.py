from motor.motor_asyncio import AsyncIOMotorClient

# ticket db, docker-compose'da ayarladığımız standart port üzerinde.
MONGO_URL = "mongodb://ticket_db:27017"

client = AsyncIOMotorClient(MONGO_URL)
database = client.ticket_db
ticket_collection = database.get_collection("tickets")