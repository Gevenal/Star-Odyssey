"""Save/load game endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas import (
    SaveGameRequest,
    SaveGameResponse,
    ListSavesResponse,
    LoadGameResponse,
)
from app.api.deps import get_state_manager

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
    state_manager=Depends(get_state_manager)
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
        HTTPException 409: If save name already exists
        HTTPException 400: If game has ended (cannot save ended games)
    """
    # TODO: Implement save functionality
    # game_state = await state_manager.get_state(request.session_id)
    # if not game_state:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Session {request.session_id} not found"
    #     )

    # if game_state.is_game_over():
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Cannot save ended game"
    #     )

    # save_id = await state_manager.save_checkpoint(
    #     session_id=request.session_id,
    #     save_name=request.save_name,
    #     description=request.description
    # )

    # return SaveGameResponse(
    #     save_id=save_id,
    #     save_name=request.save_name,
    #     saved_at=datetime.utcnow().isoformat(),
    #     turn_count=game_state.turn_count
    # )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Save functionality not yet implemented"
    )


@router.get(
    "/saves",
    response_model=ListSavesResponse,
    summary="List saves",
    description="List all saved games with metadata."
)
async def list_saves(
    state_manager=Depends(get_state_manager)
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
        state_manager: StateManager dependency

    Returns:
        ListSavesResponse with list of save metadata
    """
    # TODO: Implement save listing
    # saves = await save_repo.list_saves()
    # save_metadata = [
    #     SaveMetadata(
    #         save_id=save["_id"],
    #         save_name=save["save_name"],
    #         description=save.get("description"),
    #         saved_at=save["saved_at"],
    #         turn_count=save["turn_count"],
    #         day=save["day"],
    #         player_name=save["player_name"],
    #         alive_npcs=save["alive_npcs"],
    #         ending_triggered=save.get("ending_triggered")
    #     )
    #     for save in saves
    # ]
    # return ListSavesResponse(saves=save_metadata, total=len(save_metadata))

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List saves not yet implemented"
    )


@router.post(
    "/load/{save_id}",
    response_model=LoadGameResponse,
    summary="Load saved game",
    description="Load a saved game and create a new session."
)
async def load_game(
    save_id: str,
    state_manager=Depends(get_state_manager)
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
    # TODO: Implement load functionality
    # session_id = await state_manager.restore_checkpoint(save_id)
    # if not session_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Save {save_id} not found"
    #     )

    # game_state = await state_manager.get_state(session_id)
    # narration = await generate_load_narration(game_state)

    # return LoadGameResponse(
    #     session_id=session_id,
    #     game_state=game_state,
    #     narration=narration,
    #     available_actions=await get_available_actions(game_state)
    # )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Save {save_id} not found (not yet implemented)"
    )


@router.delete(
    "/save/{save_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete saved game",
    description="Permanently delete a saved game."
)
async def delete_save(
    save_id: str,
    state_manager=Depends(get_state_manager)
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
    # TODO: Implement save deletion
    # deleted = await save_repo.delete(save_id)
    # if not deleted:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Save {save_id} not found"
    #     )
    # return None

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Save {save_id} not found (not yet implemented)"
    )
