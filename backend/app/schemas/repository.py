from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str  # "file" or "directory"
    size_bytes: int = 0
    language: Optional[str] = None
    children: Optional[List['FileTreeNode']] = None

class RepoScanRequest(BaseModel):
    workspace_id: str
    path: str

class RepoSummaryResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    path: str
    is_git: bool
    default_branch: str
    languages: Dict[str, int]
    frameworks: List[str]
    file_count: int
    total_size_bytes: int
    top_dependencies: List[str] = Field(default_factory=list)

class FileContentResponse(BaseModel):
    file_path: str
    relative_path: str
    language: str
    line_count: int
    size_bytes: int
    content: str
    truncated: bool = False

class SymbolItem(BaseModel):
    name: str
    kind: str  # "function", "class", "async_def", "interface", "variable"
    line_start: int
    line_end: int
    docstring: Optional[str] = None

class FileSymbolsResponse(BaseModel):
    file_path: str
    symbols: List[SymbolItem]

class SearchMatch(BaseModel):
    line_number: int
    line_text: str

class SearchResultItem(BaseModel):
    file_path: str
    relative_path: str
    language: str
    matches: List[SearchMatch]

class CodeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = 50

class CodeSearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[SearchResultItem]

class ContextRetrievalRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    max_tokens: int = 8000
    max_files: int = 10

class RelevantFileContext(BaseModel):
    file_path: str
    relative_path: str
    language: str
    relevance_score: float
    relevance_reason: str
    content: str
    token_estimate: int

class ContextRetrievalResponse(BaseModel):
    total_files_ranked: int
    selected_files: List[RelevantFileContext]
    total_tokens_estimated: int

class CallSiteItem(BaseModel):
    calling_file: str
    line_number: int
    line_text: str
    callee_symbol: str

class CrossFileSymbolMap(BaseModel):
    symbol_name: str
    defining_file: str
    kind: str
    line: int
    docstring: Optional[str] = None
    call_sites: List[CallSiteItem] = Field(default_factory=list)

class DependencyGraphResponse(BaseModel):
    nodes: List[str]
    edges: List[Dict[str, str]] = Field(default_factory=list, description="source -> target")
    dependency_counts: Dict[str, int] = Field(default_factory=dict)
    isolated_files: List[str] = Field(default_factory=list)

class ChangeImpactReport(BaseModel):
    target_file: str
    directly_impacted_files: List[str]
    transitively_impacted_files: List[str]
    associated_test_files: List[str]
    risk_level: str  # LOW | MEDIUM | HIGH
    summary: str

