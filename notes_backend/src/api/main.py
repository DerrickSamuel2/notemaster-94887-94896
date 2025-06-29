import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file (recommended for config)
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception(
        "Missing Supabase configuration. Please set SUPABASE_URL and "
        "SUPABASE_KEY in the environment."
    )


def get_supabase_client() -> Client:
    """Get a Supabase client instance."""
    # PUBLIC_INTERFACE
    return create_client(SUPABASE_URL, SUPABASE_KEY)


class NoteBase(BaseModel):
    title: str = Field(..., description="Title of the note")
    content: Optional[str] = Field("", description="Content/body of the note")


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated title of the note")
    content: Optional[str] = Field(None, description="Updated content/body of the note")


class Note(NoteBase):
    id: int = Field(..., description="Unique ID for the note")

    class Config:
        orm_mode = True


app = FastAPI(
    title="Notes Backend",
    description=(
        "A FastAPI backend for managing notes with CRUD operations, "
        "connecting to Supabase for database operations.\n\n"
        "OpenAPI documentation for the fullstack notes application."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "notes", "description": "Operations to manage notes"},
        {"name": "health", "description": "Service health endpoints"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


NOTES_TABLE = "notes"


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Verify that the notes backend is running.",
)
def health_check():
    """
    Returns a simple health check message.
    """
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/notes",
    response_model=Note,
    status_code=201,
    summary="Create a new note",
    tags=["notes"],
    description="Create a new note with a title and optional content.",
)
def create_note(note: NoteCreate, supabase: Client = Depends(get_supabase_client)):
    """
    Create a new note and return the created note.
    """
    data = {
        "title": note.title,
        "content": note.content,
    }
    response = supabase.table(NOTES_TABLE).insert(data).execute()
    if response.error:
        raise HTTPException(
            status_code=500, detail=f"Failed to create note: {response.error.message}"
        )
    created = response.data[0]
    return Note(
        id=created["id"], title=created["title"], content=created.get("content") or ""
    )


# PUBLIC_INTERFACE
@app.get(
    "/notes",
    response_model=List[Note],
    summary="List all notes",
    tags=["notes"],
    description="Retrieve a list of all notes.",
)
def list_notes(supabase: Client = Depends(get_supabase_client)):
    """
    Fetch and return all notes.
    """
    response = supabase.table(NOTES_TABLE).select("*").order("id", desc=False).execute()
    if response.error:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch notes: {response.error.message}"
        )
    return [
        Note(
            id=note["id"],
            title=note["title"],
            content=note.get("content") or "",
        )
        for note in response.data
    ]


# PUBLIC_INTERFACE
@app.get(
    "/notes/{note_id}",
    response_model=Note,
    summary="Get a single note",
    tags=["notes"],
    description="Fetch a single note by its ID.",
)
def get_note(note_id: int, supabase: Client = Depends(get_supabase_client)):
    """
    Fetch a single note by its ID.
    """
    response = (
        supabase.table(NOTES_TABLE).select("*").eq("id", note_id).single().execute()
    )
    if response.error:
        if response.status_code == 406:
            raise HTTPException(status_code=404, detail="Note not found")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve note: {response.error.message}"
        )
    note = response.data
    return Note(
        id=note["id"], title=note["title"], content=note.get("content") or ""
    )


# PUBLIC_INTERFACE
@app.put(
    "/notes/{note_id}",
    response_model=Note,
    summary="Update a note",
    tags=["notes"],
    description="Update an existing note by its ID.",
)
def update_note(note_id: int, note: NoteUpdate, supabase: Client = Depends(get_supabase_client)):
    """
    Update the title and/or content of a note.
    """
    update_data = {}
    if note.title is not None:
        update_data["title"] = note.title
    if note.content is not None:
        update_data["content"] = note.content
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update.")
    response = (
        supabase.table(NOTES_TABLE).update(update_data).eq("id", note_id).execute()
    )
    if response.error:
        raise HTTPException(
            status_code=500, detail=f"Failed to update note: {response.error.message}"
        )
    if not response.data:
        raise HTTPException(status_code=404, detail="Note not found")
    updated = response.data[0]
    return Note(
        id=updated["id"], title=updated["title"], content=updated.get("content") or ""
    )


# PUBLIC_INTERFACE
@app.delete(
    "/notes/{note_id}",
    status_code=204,
    summary="Delete a note",
    tags=["notes"],
    description="Delete a note by its ID. Returns no content on success.",
)
def delete_note(note_id: int, supabase: Client = Depends(get_supabase_client)):
    """
    Delete a note by its ID.
    """
    response = (
        supabase.table(NOTES_TABLE).delete().eq("id", note_id).execute()
    )
    if response.error:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete note: {response.error.message}"
        )
    if not response.data:
        raise HTTPException(status_code=404, detail="Note not found")
    return


# PUBLIC_INTERFACE
@app.get(
    "/docs/ws",
    tags=["health"],
    summary="WebSocket usage",
    description="Information on current WebSocket usage in this project (None for this API).",
)
def ws_info():
    """
    This notes backend does not use WebSockets.
    """
    return {"message": "No WebSocket endpoints provided in this API."}


"""
Supabase Table: notes
Columns:
- id: integer, primary key, auto-increment
- title: text, not null
- content: text, nullable

You may initialize this table in Supabase via the dashboard or SQL:
CREATE TABLE notes (
    id serial PRIMARY KEY,
    title text NOT NULL,
    content text
);
"""
