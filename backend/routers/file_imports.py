from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models.user import User
from schemas.day11_mcp import BrainDumpFileImportResponse, MCPServerInspectResponse, MCPToolInfo
from services.brain_dump_service import create_brain_dump, process_brain_dump
from services.mcp_file_client import read_file_through_mcp
from services.mcp_tool_decision_service import choose_import_tool


router = APIRouter(prefix="/file-imports", tags=["file-imports"])
BACKEND_DIR = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.getenv("THOUGHTLINKER_MCP_WORKSPACE", str(BACKEND_DIR / "mcp_workspace" / "imports"))).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_BYTES = 2 * 1024 * 1024


@router.get("/mcp/inspect", response_model=MCPServerInspectResponse)
def inspect_mcp_server(current_user: User = Depends(get_current_user)):
    return MCPServerInspectResponse(
        server_name="ThoughtLinker Local File Server",
        transport="stdio",
        tools=["read_local_text_file"],
        supported_extensions=sorted(ALLOWED_EXTENSIONS),
        max_file_bytes=MAX_FILE_BYTES,
    )


@router.post("/brain-dump", response_model=BrainDumpFileImportResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_file_as_brain_dump(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    instruction: str = Form("Import this file into my notes."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_name = Path(file.filename or "import.txt").name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only .txt and .md files can be imported.")

    raw = await file.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="The file exceeds the 2 MB import limit.")
    if not raw:
        raise HTTPException(status_code=422, detail="The imported file is empty.")

    stored_name = f"{uuid.uuid4().hex}{extension}"
    stored_path = WORKSPACE / stored_name
    stored_path.write_bytes(raw)

    try:
        decision = choose_import_tool(original_name, instruction)
        if not decision.use_tool or decision.tool_name != "read_local_text_file":
            raise HTTPException(status_code=422, detail="The model did not select the local-file reader for this request.")

        tool_result = await read_file_through_mcp(stored_name)
        imported_text = tool_result.content.strip()
        if len(imported_text) > 20_000:
            imported_text = imported_text[:20_000]

        brain_dump = create_brain_dump(db=db, user_id=current_user.id, raw_text=imported_text)
        background_tasks.add_task(process_brain_dump, brain_dump.id)

        return BrainDumpFileImportResponse(
            brain_dump_id=brain_dump.id,
            status=brain_dump.status,
            imported_text=imported_text,
            tool=MCPToolInfo(
                tool_name=tool_result.tool_name,
                chosen_by=decision.chosen_by,
                reason=decision.reason,
                file_name=original_name,
                extension=tool_result.extension,
                characters=tool_result.characters,
            ),
            created_at=brain_dump.created_at,
        )
    finally:
        stored_path.unlink(missing_ok=True)
