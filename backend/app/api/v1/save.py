"""Save/load game endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas import (
    SaveGameRequest,
    SaveGameResponse,
    SaveMetadata,
    ListSavesResponse,
    LoadGameResponse,
)
from app.api.deps import get_session_manager
from app.utils.state_converter import StateConverter

router = APIRouter()


@router.post(
    "/save",
    response_model=SaveGameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save game",
    description="Save the current game state with a custom name."
)
async def save_game(
    request: SaveGameRequest,
    state_manager=Depends(get_session_manager)
) -> SaveGameResponse:
    """
    Save current game state.

    Creates a checkpoint of the current game state that can be loaded later.
    Includes all game data: player state, NPC states, world state, history.

    Args:
        request: Save request with session_id and save name
        state_manager: StateManager dependency

    Returns:
        SaveGameResponse with save_id and metadata

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If game has ended (cannot save ended games)
    """
    try:
        # Get current game state
        game_state_snapshot = await state_manager.get_state(request.session_id)
        
        # Check if game has ended
        game_phase = game_state_snapshot.get("state", {}).get("game_meta", {}).get("game_phase", "playing")
        if game_phase == "ended":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot save ended game"
            )
        
        # Create checkpoint
        save_id = await state_manager.save_checkpoint(
            session_id=request.session_id,
            checkpoint_name=request.save_name
        )
        
        # Get turn count from state
        turn_count = game_state_snapshot.get("turn", 0)
        
        return SaveGameResponse(
            save_id=save_id,
            save_name=request.save_name,
            saved_at=datetime.utcnow().isoformat(),
            turn_count=turn_count
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save game: {str(e)}"
        )


@router.get(
    "/saves",
    response_model=ListSavesResponse,
    summary="List saves",
    description="List all saved games with metadata."
)
async def list_saves(
    session_id: str = None,
    state_manager=Depends(get_session_manager)
) -> ListSavesResponse:
    """
    List all saved games.

    Returns metadata for all saved games including:
    - Save ID and name
    - When saved
    - Turn count and game day
    - Player name
    - Number of living NPCs
    - Whether game had ended

    Args:
        session_id: Optional session_id to filter saves
        state_manager: StateManager dependency

    Returns:
        ListSavesResponse with list of save metadata
    """
    try:
        # Query checkpoints collection directly
        query = {}
        if session_id:
            query["session_id"] = session_id
        
        cursor = state_manager.checkpoints.find(query).sort("created_at", -1)
        
        save_metadata_list = []
        async for doc in cursor:
            # Extract state info for metadata
            saved_state = doc.get("state", {})
            state_data = saved_state.get("state", {})
            
            # Get player info
            player_name = state_data.get("player", {}).get("name", "Unknown")
            
            # Count living NPCs
            npcs = state_data.get("npcs", {})
            alive_npcs = sum(1 for npc in npcs.values() if npc.get("alive", True))
            
            # Get game day
            day = state_data.get("world", {}).get("current_day", 1)
            
            # Get ending status
            game_meta = state_data.get("game_meta", {})
            ending_triggered = game_meta.get("ending_id") if game_meta.get("game_phase") == "ended" else None
            
            save_metadata_list.append(SaveMetadata(
                save_id=doc["_id"],
                save_name=doc.get("name", "Unnamed Save"),
                description=None,
                saved_at=doc["created_at"].isoformat() if doc.get("created_at") else "",
                turn_count=doc.get("turn", 0),
                day=day,
                player_name=player_name,
                alive_npcs=alive_npcs,
                ending_triggered=ending_triggered
            ))
        
        return ListSavesResponse(saves=save_metadata_list, total=len(save_metadata_list))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list saves: {str(e)}"
        )


@router.post(
    "/load/{save_id}",
    response_model=LoadGameResponse,
    summary="Load saved game",
    description="Load a saved game and create a new session."
)
async def load_game(
    save_id: str,
    state_manager=Depends(get_session_manager)
) -> LoadGameResponse:
    """
    Load a saved game.

    Creates a new session from a saved game checkpoint.
    Restores all game state including player, NPCs, world, and history.

    Args:
        save_id: Save identifier
        state_manager: StateManager dependency

    Returns:
        LoadGameResponse with new session_id and restored state

    Raises:
        HTTPException 404: If save not found
    """
    try:
        # Restore checkpoint (creates new session)
        new_session_id = await state_manager.restore_checkpoint(save_id)
        
        # Get the restored state
        game_state_snapshot = await state_manager.get_state(new_session_id)
        
        # Convert to Pydantic model
        game_state = StateConverter.snapshot_to_game_state(game_state_snapshot, new_session_id)
        
        # Generate load narration
        player_name = game_state_snapshot.get("state", {}).get("player", {}).get("name", "Survivor")
        turn = game_state_snapshot.get("turn", 0)
        location = game_state_snapshot.get("state", {}).get("player", {}).get("current_location", "unknown")
        narration = f"Returning to the Odyssey-7... {player_name} awakens, memories flooding back. It's turn {turn}, and you find yourself in the {location.replace('_', ' ')}."
        
        # Get available actions (simplified - just return common actions)
        available_actions = ["explore_area", "check_systems", "talk_to_oracle", "rest"]
        
        return LoadGameResponse(
            session_id=new_session_id,
            game_state=game_state,
            narration=narration,
            available_actions=available_actions
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load game: {str(e)}"
        )


@router.delete(
    "/save/{save_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete saved game",
    description="Permanently delete a saved game."
)
async def delete_save(
    save_id: str,
    state_manager=Depends(get_session_manager)
):
    """
    Delete a saved game.

    Permanently removes the save from storage.
    This action cannot be undone.

    Args:
        save_id: Save identifier
        state_manager: StateManager dependency

    Returns:
        No content (204)

    Raises:
        HTTPException 404: If save not found
    """
    try:
        # Delete from checkpoints collection
        result = await state_manager.checkpoints.delete_one({"_id": save_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Save {save_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete save: {str(e)}"
        )
