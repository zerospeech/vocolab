from pydantic import BaseModel


class LeaderboardPublicView(BaseModel):
    id: int
    challenge_id: int
    label: str
    entry_file: str
    archived: bool
    static_files: bool
