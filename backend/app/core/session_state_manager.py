"""
Session State Manager - Game Session Persistence
Responsible for managing game sessions and database persistence
"""
from typing import Optional, Dict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from app.config import settings
from .game_state_manager import GameStateManager


class SessionStateManager:
    """
    Session State Manager (Database Persistence Layer)
    
    Responsibilities:
    1. Create and manage game sessions
    2. Persist game state to MongoDB
    3. Support checkpoint system (save points)
    4. Support Redis caching (optional)
    
    Not Responsible For:
    - Game rules and logic
    - State validation
    - AI interaction
    """
    
    def __init__(self, mongo_client: AsyncIOMotorClient, redis_cache=None):
        """
        Initialize session manager
        
        Args:
            mongo_client: Motor async MongoDB client
            redis_cache: Redis cache client (optional)
        """
        self.mongo_client = mongo_client
        self.db = mongo_client[settings.mongodb_db_name]
        
        # Collections
        self.sessions = self.db["sessions"]
        self.checkpoints = self.db["checkpoints"]
        
        # Redis cache (optional)
        self.redis_cache = redis_cache

        # Config directory for GameStateManager (app/game_data)
        self.config_dir = str(settings.config_directory)
    
    async def create_session(self, player_name: str) -> str:
        """
        Create a new game session
        
        Args:
            player_name: Player's name
            
        Returns:
            str: Newly created session_id
            
        Workflow:
        1. Create new GameStateManager instance (get initial state)
        2. Generate unique session_id
        3. Save to MongoDB
        4. Optional: Write to Redis cache
        """
        # 1. Create initial game state
        game_state = GameStateManager(config_dir=self.config_dir)
        game_state.set("player.name", player_name, validate=False)
        
        initial_snapshot = game_state.get_snapshot()
        
        # 2. Generate session_id
        session_id = str(uuid.uuid4())
        
        # 3. Prepare session document
        session_doc = {
            "_id": session_id,
            "player_name": player_name,
            "state": initial_snapshot,
            "created_at": datetime.utcnow(),
            "last_played": datetime.utcnow(),
            "current_turn": 0,
            "game_phase": "intro",
            "is_active": True
        }
        
        # 4. Save to MongoDB
        await self.sessions.insert_one(session_doc)
        
        # 5. Optional: Write to Redis cache
        if self.redis_cache:
            await self.set_cache(session_id, initial_snapshot)
        
        print(f"[SessionManager] Created new session: {session_id} for player: {player_name}")
        return session_id



    async def get_state(self, session_id: str) -> Dict:
        """
        Get game state
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict: Game state snapshot
            
        Lookup order:
        1. Check Redis cache first (if enabled)
        2. Then check MongoDB
        
        Raises:
            ValueError: If session doesn't exist
        """
        # 1. Try to get from cache
        if self.redis_cache:
            cached_state = await self.get_from_cache(session_id)
            if cached_state:
                print(f"[SessionManager] Cache hit for session: {session_id}")
                return cached_state
        
        # 2. Get from MongoDB
        doc = await self.sessions.find_one({"_id": session_id})
        
        if not doc:
            raise ValueError(f"Session {session_id} not found")
        
        state = doc["state"]
        
        # 3. Write to cache (faster next time)
        if self.redis_cache:
            await self.set_cache(session_id, state)
        
        return state
    
    async def update_state(self, session_id: str, snapshot: Dict) -> bool:
        """
        Update game state
        
        Args:
            session_id: Session ID
            snapshot: Game state snapshot (from GameStateManager.get_snapshot())
            
        Returns:
            bool: Whether update was successful
            
        Workflow:
        1. Update MongoDB
        2. Update Redis cache (if enabled)
        3. Update metadata (last_played, current_turn, etc.)
        """
        # Extract metadata
        current_turn = snapshot.get("turn", 0)
        game_phase = snapshot.get("state", {}).get("game_meta", {}).get("game_phase", "playing")
        
        # Update MongoDB
        result = await self.sessions.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "state": snapshot,
                    "last_played": datetime.utcnow(),
                    "current_turn": current_turn,
                    "game_phase": game_phase
                }
            }
        )
        
        if result.modified_count == 0:
            print(f"[SessionManager] Warning: Session {session_id} not updated (maybe not found)")
            return False
        
        # Update cache
        if self.redis_cache:
            await self.set_cache(session_id, snapshot)
        
        print(f"[SessionManager] Session {session_id} updated (Turn {current_turn})")
        return True
    
    async def save_checkpoint(self, session_id: str, checkpoint_name: str = None) -> str:
        """
        Create a checkpoint (save point)
        
        Args:
            session_id: Session ID
            checkpoint_name: Checkpoint name (optional)
            
        Returns:
            str: Checkpoint ID
            
        Use cases:
        - Player manual save
        - Auto-save at important story points
        - For player to load later
        """
        # 1. Get current state
        current_state = await self.get_state(session_id)
        
        # 2. Generate checkpoint_id
        timestamp = datetime.utcnow().isoformat()
        checkpoint_id = f"{session_id}_{timestamp}"
        
        # 3. Prepare checkpoint document
        checkpoint_doc = {
            "_id": checkpoint_id,
            "session_id": session_id,
            "name": checkpoint_name or f"Auto Save - Turn {current_state.get('turn', 0)}",
            "state": current_state,
            "created_at": datetime.utcnow(),
            "turn": current_state.get("turn", 0)
        }
        
        # 4. Save to checkpoints collection
        await self.checkpoints.insert_one(checkpoint_doc)
        
        print(f"[SessionManager] Checkpoint created: {checkpoint_id}")
        return checkpoint_id
    
    async def restore_checkpoint(self, checkpoint_id: str) -> str:
        """
        Restore game from checkpoint
        
        Args:
            checkpoint_id: Checkpoint ID
            
        Returns:
            str: New session_id (creates new session after restore)
            
        Workflow:
        1. Read checkpoint from checkpoints collection
        2. Create new session (avoid overwriting original game)
        3. Return new session_id
        
        Raises:
            ValueError: If checkpoint doesn't exist
        """
        # 1. Get checkpoint
        checkpoint = await self.checkpoints.find_one({"_id": checkpoint_id})
        
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        # 2. Extract state and player info
        saved_state = checkpoint["state"]
        player_name = saved_state.get("state", {}).get("player", {}).get("name", "Unknown")
        
        # 3. Create new session
        new_session_id = str(uuid.uuid4())
        
        session_doc = {
            "_id": new_session_id,
            "player_name": player_name,
            "state": saved_state,
            "created_at": datetime.utcnow(),
            "last_played": datetime.utcnow(),
            "current_turn": checkpoint.get("turn", 0),
            "game_phase": saved_state.get("state", {}).get("game_meta", {}).get("game_phase", "playing"),
            "is_active": True,
            "restored_from": checkpoint_id
        }
        
        await self.sessions.insert_one(session_doc)
        
        # 4. Optional: Write to cache
        if self.redis_cache:
            await self.set_cache(new_session_id, saved_state)
        
        print(f"[SessionManager] Checkpoint {checkpoint_id} restored to new session: {new_session_id}")
        return new_session_id
    
    async def delete_session(self, session_id: str):
        """
        Delete game session
        
        Args:
            session_id: Session ID
            
        Workflow:
        1. Delete session document
        2. Delete related checkpoints
        3. Clear Redis cache (if enabled)
        """
        # 1. Delete session
        result = await self.sessions.delete_one({"_id": session_id})
        
        if result.deleted_count == 0:
            print(f"[SessionManager] Warning: Session {session_id} not found for deletion")
            return
        
        # 2. Delete related checkpoints
        checkpoint_result = await self.checkpoints.delete_many({"session_id": session_id})
        print(f"[SessionManager] Deleted {checkpoint_result.deleted_count} checkpoints for session {session_id}")
        
        # 3. Clear cache
        if self.redis_cache:
            await self.redis_cache.delete(f"session:{session_id}")
        
        print(f"[SessionManager] Session {session_id} deleted")
    
    async def get_from_cache(self, session_id: str) -> Optional[Dict]:
        """
        Get state from Redis cache
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[Dict]: Cached state, or None if not found
        """
        if not self.redis_cache:
            return None
        
        try:
            import json
            cache_key = f"session:{session_id}"
            cached_data = await self.redis_cache.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return None
        except Exception as e:
            print(f"[SessionManager] Redis cache error: {e}")
            return None
    
    async def set_cache(self, session_id: str, state_data: Dict, ttl: int = 3600):
        """
        Set Redis cache
        
        Args:
            session_id: Session ID
            state_data: State data
            ttl: Cache expiration time (seconds), default 1 hour
        """
        if not self.redis_cache:
            return
        
        try:
            import json
            cache_key = f"session:{session_id}"
            await self.redis_cache.setex(
                cache_key,
                ttl,
                json.dumps(state_data)
            )
        except Exception as e:
            print(f"[SessionManager] Redis cache write error: {e}")
    
    async def list_sessions(self, player_name: str = None, limit: int = 10) -> list:
        """
        List game sessions (for "Continue Game" feature)
        
        Args:
            player_name: Optional, filter by specific player
            limit: Number of sessions to return
            
        Returns:
            list: Session list
        """
        query = {"is_active": True}
        if player_name:
            query["player_name"] = player_name
        
        cursor = self.sessions.find(query).sort("last_played", -1).limit(limit)
        
        sessions = []
        async for doc in cursor:
            sessions.append({
                "session_id": doc["_id"],
                "player_name": doc["player_name"],
                "current_turn": doc["current_turn"],
                "game_phase": doc["game_phase"],
                "last_played": doc["last_played"],
                "created_at": doc["created_at"]
            })
        
        return sessions
    
    async def get_checkpoints(self, session_id: str) -> list:
        """
        Get all checkpoints for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            list: Checkpoint list
        """
        cursor = self.checkpoints.find({"session_id": session_id}).sort("created_at", -1)
        
        checkpoints = []
        async for doc in cursor:
            checkpoints.append({
                "checkpoint_id": doc["_id"],
                "name": doc["name"],
                "turn": doc["turn"],
                "created_at": doc["created_at"]
            })
        
        return checkpoints


# ===== Initialization Helper =====

async def init_mongodb_indexes(session_manager: SessionStateManager):
    """
    Initialize MongoDB indexes (improve query performance)
    
    Should be called once during application startup
    """
    # Sessions collection indexes
    await session_manager.sessions.create_index("player_name")
    await session_manager.sessions.create_index("last_played")
    await session_manager.sessions.create_index([("is_active", 1), ("last_played", -1)])
    
    # Checkpoints collection indexes
    await session_manager.checkpoints.create_index("session_id")
    await session_manager.checkpoints.create_index("created_at")
    
    print("[SessionManager] MongoDB indexes created")


# ===== Usage Example =====
if __name__ == "__main__":
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    
    async def test():
        # 1. Connect to MongoDB
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        session_mgr = SessionStateManager(client)
        
        # Initialize indexes
        await init_mongodb_indexes(session_mgr)
        
        # 2. Create new game
        session_id = await session_mgr.create_session("Yifan")
        print(f"✅ Session created: {session_id}")
        
        # 3. Load state
        state = await session_mgr.get_state(session_id)
        print(f"✅ State loaded, oxygen: {state['state']['resources']['oxygen_level']}")
        
        # 4. Modify state (simulate GameLoop)
        from game_state_manager import GameStateManager
        game_state = GameStateManager()
        game_state.load_snapshot(state)
        
        game_state.modify("resources.oxygen_level", -10)
        print(f"✅ Oxygen modified to: {game_state.get('resources.oxygen_level')}")
        
        # 5. Save back to database
        snapshot = game_state.get_snapshot()
        success = await session_mgr.update_state(session_id, snapshot)
        print(f"✅ State saved: {success}")
        
        # 6. Create checkpoint
        checkpoint_id = await session_mgr.save_checkpoint(session_id, "Test Save")
        print(f"✅ Checkpoint created: {checkpoint_id}")
        
        # 7. List sessions
        sessions = await session_mgr.list_sessions()
        print(f"✅ Found {len(sessions)} active sessions")
        
        # 8. Cleanup
        # await session_mgr.delete_session(session_id)
        # print(f"✅ Session deleted")
        
        print("\n🎉 All tests passed!")
    
    asyncio.run(test())