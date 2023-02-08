from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field, AnyHttpUrl


class EntryDetails(BaseModel):
    train_set: Optional[str]
    benchmarks: List[str]
    gpu_budget: Optional[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)

class PublicationEntry(BaseModel):
    author_short: Optional[str]
    authors: Optional[str]
    paper_title: Optional[str]
    paper_ref: Optional[str]
    bib_ref: Optional[str]
    paper_url: Optional[Union[AnyHttpUrl, str]]
    pub_year: Optional[int]
    team_name: Optional[str]
    institution: str
    code: Optional[Union[AnyHttpUrl, str]]
    DOI: Optional[str]
    open_science: bool = False

class LeaderboardEntryItem(BaseModel):
    model_id: Optional[str]
    submission_id: str = ""
    index: Optional[int]
    submission_date: Optional[datetime]
    submitted_by: Optional[str]
    description: str
    publication: PublicationEntry
    details: EntryDetails
    scores: Any
    extras: Optional[Dict[str, Any]]



class LeaderboardObj(BaseModel):
    updatedOn: datetime
    data: List[LeaderboardEntryItem]
    sorting_key: Optional[str]

