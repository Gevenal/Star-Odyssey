"""Base repository abstraction."""
from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase


class BaseRepository(ABC):
    """Abstract base repository for data access."""

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        """
        Initialize repository.

        Args:
            db: Database instance
            collection_name: MongoDB collection name
        """
        self.db = db
        self.collection_name = collection_name
        self.collection = db[collection_name]

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> str:
        """
        Create new document.

        Args:
            data: Document data

        Returns:
            str: Created document ID
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            id: Document ID

        Returns:
            Optional[dict]: Document or None
        """
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """
        Update document.

        Args:
            id: Document ID
            data: Update data

        Returns:
            bool: True if updated
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete document.

        Args:
            id: Document ID

        Returns:
            bool: True if deleted
        """
        pass

    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find documents matching query.

        Args:
            query: MongoDB query

        Returns:
            list[dict]: Matching documents
        """
        raise NotImplementedError

    async def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents.

        Args:
            query: Optional query filter

        Returns:
            int: Document count
        """
        raise NotImplementedError
