import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


class DataBase:
    client: AsyncIOMotorClient = None


db = DataBase()


def get_mongo_uri() -> str:
    """Load environment variables and create MongoDB URI"""
    load_dotenv()
    mongo_username = os.environ.get('MONGO_INITDB_ROOT_USERNAME')
    mongo_password = os.environ.get('MONGO_INITDB_ROOT_PASSWORD')
    mongo_host = os.environ.get('MONGO_HOST')
    mongo_port = os.environ.get('MONGO_PORT')
    mongo_uri = f'mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}'
    return mongo_uri


async def get_database(db_name: str = 'articles') -> AsyncIOMotorClient:
    """Returns an asynchronous DB client"""
    return db.client[db_name]


async def startup_db_client() -> None:
    """Start DB client"""
    db.client = AsyncIOMotorClient(get_mongo_uri())


async def shutdown_db_client() -> None:
    """Shutdown DB client"""
    db.client.close()
