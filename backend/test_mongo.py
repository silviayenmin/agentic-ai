import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    uri = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2000)
    try:
        await client.admin.command('ping')
        print("SUCCESS: Connected to MongoDB")
    except Exception as e:
        print(f"FAILED: Could not connect to MongoDB: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
