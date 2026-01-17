"""MongoDB connection and client."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBClient:
    """MongoDB client singleton."""

    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

    @classmethod
    async def connect(cls):
        """Initialize MongoDB connection."""
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            )
            cls.database = cls.client[settings.MONGODB_DB_NAME]

            # Verify connection
            await cls.client.admin.command("ping")
            logger.info("MongoDB connection established")

            # Create indexes
            await cls._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            logger.info("Closing MongoDB connection")
            cls.client.close()
            cls.client = None
            cls.database = None

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.database

    @classmethod
    async def _create_indexes(cls):
        """Create database indexes for performance."""
        db = cls.get_database()

        # Game sessions index
        await db.game_sessions.create_index("session_id", unique=True)
        await db.game_sessions.create_index("created_at")
        await db.game_sessions.create_index("phase")

        # Game states index
        await db.game_states.create_index("session_id", unique=True)
        await db.game_states.create_index([("session_id", 1), ("turn_count", -1)])

        # Saves index
        await db.saves.create_index("save_id", unique=True)
        await db.saves.create_index("session_id")
        await db.saves.create_index("created_at")

        # NPCs index
        await db.npcs.create_index([("session_id", 1), ("npc_id", 1)], unique=True)
        await db.npcs.create_index("session_id")

        logger.info("Database indexes created")


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency for getting database."""
    return MongoDBClient.get_database()
