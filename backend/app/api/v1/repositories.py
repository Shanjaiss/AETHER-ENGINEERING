from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.workspace import Workspace, Repository
from backend.app.schemas.repository import (
    RepoScanRequest,
    RepoSummaryResponse,
    FileTreeNode,
    FileContentResponse,
    FileSymbolsResponse,
    CodeSearchRequest,
    CodeSearchResponse,
    ContextRetrievalRequest,
    ContextRetrievalResponse,
    CallSiteItem,
    CrossFileSymbolMap,
    DependencyGraphResponse,
    ChangeImpactReport
)
from backend.app.services.repo_intelligence.scanner import RepositoryScanner

router = APIRouter()

def get_repository_or_404(repo_id: str, db: Session) -> Repository:
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repo

@router.post("/scan", response_model=RepoSummaryResponse, summary="Scan and index a repository")
def scan_repository(payload: RepoScanRequest, db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    scanner = RepositoryScanner(Path(payload.path))
    summary = scanner.scan_summary()

    # Create or update repository record
    repo = db.query(Repository).filter(Repository.workspace_id == workspace.id).first()
    if not repo:
        repo = Repository(
            workspace_id=workspace.id,
            name=summary["name"],
            path=summary["path"],
            is_git=summary["is_git"],
            default_branch=summary["default_branch"],
            languages=summary["languages"],
            frameworks=summary["frameworks"],
            file_count=str(summary["file_count"])
        )
        db.add(repo)
    else:
        repo.name = summary["name"]
        repo.path = summary["path"]
        repo.is_git = summary["is_git"]
        repo.default_branch = summary["default_branch"]
        repo.languages = summary["languages"]
        repo.frameworks = summary["frameworks"]
        repo.file_count = str(summary["file_count"])

    db.commit()
    db.refresh(repo)

    return RepoSummaryResponse(
        id=repo.id,
        workspace_id=repo.workspace_id,
        name=repo.name,
        path=repo.path,
        is_git=repo.is_git,
        default_branch=repo.default_branch,
        languages=repo.languages,
        frameworks=repo.frameworks,
        file_count=int(repo.file_count),
        total_size_bytes=summary["total_size_bytes"],
        top_dependencies=summary["top_dependencies"]
    )

@router.get("/{repo_id}/tree", response_model=FileTreeNode, summary="Get hierarchical file tree")
def get_file_tree(repo_id: str, max_depth: int = Query(5, ge=1, le=10), db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    return scanner.build_file_tree(max_depth=max_depth)

@router.get("/{repo_id}/file", response_model=FileContentResponse, summary="Inspect safe file content")
def inspect_file(repo_id: str, path: str = Query(..., description="Relative file path"), db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    result = scanner.read_safe_file(path)
    return FileContentResponse(**result)

@router.get("/{repo_id}/symbols", response_model=FileSymbolsResponse, summary="Extract AST symbols from file")
def get_file_symbols(repo_id: str, path: str = Query(..., description="Relative file path"), db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    symbols = scanner.extract_symbols(path)
    return FileSymbolsResponse(file_path=path, symbols=symbols)

@router.post("/{repo_id}/search", response_model=CodeSearchResponse, summary="Search codebase")
def search_code(repo_id: str, payload: CodeSearchRequest, db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    results = scanner.search_code(payload.query, max_results=payload.max_results)
    total_matches = sum(len(r.matches) for r in results)
    return CodeSearchResponse(
        query=payload.query,
        total_matches=total_matches,
        results=results
    )

@router.post("/{repo_id}/context", response_model=ContextRetrievalResponse, summary="Retrieve ranked context files")
def retrieve_context(repo_id: str, payload: ContextRetrievalRequest, db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    relevant_files = scanner.retrieve_context(
        prompt=payload.prompt,
        max_tokens=payload.max_tokens,
        max_files=payload.max_files
    )
    total_tokens = sum(f.token_estimate for f in relevant_files)
    return ContextRetrievalResponse(
        total_files_ranked=len(relevant_files),
        selected_files=relevant_files,
        total_tokens_estimated=total_tokens
    )

@router.get("/{repo_id}/dependencies", response_model=DependencyGraphResponse, summary="Extract module and file dependency graph")
def get_dependencies(repo_id: str, db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    return scanner.build_dependency_graph()

@router.get("/{repo_id}/cross-file-symbols", response_model=List[CrossFileSymbolMap], summary="Discover cross-file symbols and their external call sites")
def get_cross_file_symbols(repo_id: str, db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    return scanner.discover_cross_file_symbols()

@router.get("/{repo_id}/call-sites", response_model=List[CallSiteItem], summary="Locate all call sites for a given symbol across the codebase")
def get_call_sites(repo_id: str, symbol: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    return scanner.locate_call_sites(symbol)

@router.get("/{repo_id}/change-impact", response_model=ChangeImpactReport, summary="Analyze blast radius and test requirements of modifying a file")
def get_change_impact(repo_id: str, file_path: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    repo = get_repository_or_404(repo_id, db)
    scanner = RepositoryScanner(Path(repo.path))
    return scanner.analyze_change_impact(file_path)

