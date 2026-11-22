import os
import re
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
from backend.app.schemas.repository import (
    FileTreeNode,
    SymbolItem,
    SearchResultItem,
    SearchMatch,
    RelevantFileContext,
    CallSiteItem,
    CrossFileSymbolMap,
    DependencyGraphResponse,
    ChangeImpactReport
)
from backend.app.core.security import validate_safe_path, SecurityException

# Extensions mapping to language
EXTENSION_LANGUAGE_MAP = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".json": "JSON",
    ".md": "Markdown",
    ".html": "HTML",
    ".css": "CSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".rs": "Rust",
    ".go": "Go",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header"
}

# Blocked filenames and patterns that must never be ingested (Security Rule 10)
FORBIDDEN_FILE_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"^id_(rsa|ed25519|dsa|ecdsa)(\.pub)?$", re.IGNORECASE),
    re.compile(r".*\.(pem|key|cert|p12|pfx|pkcs12|p8)$", re.IGNORECASE),
    re.compile(r".*credentials.*\.json$", re.IGNORECASE),
    re.compile(r".*secret.*", re.IGNORECASE),
    re.compile(r".*master\.key$", re.IGNORECASE),
]

# Standard ignored directory names
DEFAULT_IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".vitest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    "htmlcov",
    ".idea",
    ".vscode",
    ".next",
    ".turbo"
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar",
    ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib", ".wasm",
    ".bin", ".dat", ".db", ".sqlite", ".sqlite3"
}

class RepositoryScanner:
    """Intelligent repository discovery, AST symbol extraction, and context retrieval."""

    def __init__(self, repo_path: Path):
        self.repo_path = validate_safe_path(repo_path)
        self.gitignore_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> List[re.Pattern]:
        patterns: List[re.Pattern] = []
        gitignore_file = self.repo_path / ".gitignore"
        if gitignore_file.exists():
            try:
                with open(gitignore_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        clean_line = line.rstrip("/")
                        regex_str = (
                            clean_line.replace(".", r"\.")
                            .replace("*", ".*")
                            .replace("?", ".")
                        )
                        patterns.append(re.compile(f"(^|/){regex_str}($|/)"))
            except Exception:
                pass
        return patterns

    def is_file_ignored(self, path: Path) -> bool:
        """Check if path should be ignored according to safety rules and .gitignore."""
        if path == self.repo_path:
            return False
        rel_str = str(path.relative_to(self.repo_path))
        file_name = path.name

        # 1. Check forbidden security patterns
        for pattern in FORBIDDEN_FILE_PATTERNS:
            if pattern.match(file_name) or pattern.match(rel_str):
                return True

        # 2. Check binary extensions
        if path.suffix.lower() in BINARY_EXTENSIONS:
            return True

        # 3. Check default ignored dirs in path parts
        for part in path.parts:
            if part in DEFAULT_IGNORED_DIRS:
                return True

        # 4. Check gitignore patterns
        for pat in self.gitignore_patterns:
            if pat.search(rel_str) or pat.search(rel_str + "/"):
                return True

        return False

    def scan_summary(self) -> Dict[str, Any]:
        """Generate high-level metadata: git details, languages, frameworks, file counts."""
        is_git = (self.repo_path / ".git").exists()
        default_branch = "main"

        if is_git:
            try:
                res = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if res.returncode == 0 and res.stdout.strip():
                    default_branch = res.stdout.strip()
            except Exception:
                pass

        languages: Dict[str, int] = {}
        file_count = 0
        total_size = 0

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORED_DIRS and not self.is_file_ignored(Path(root) / d)]
            for file in files:
                fpath = Path(root) / file
                if self.is_file_ignored(fpath):
                    continue

                file_count += 1
                try:
                    size = fpath.stat().st_size
                    total_size += size
                except OSError:
                    size = 0

                ext = fpath.suffix.lower()
                lang = EXTENSION_LANGUAGE_MAP.get(ext, "Other")
                languages[lang] = languages.get(lang, 0) + 1

        frameworks, top_deps = self._detect_frameworks()

        return {
            "name": self.repo_path.name,
            "path": str(self.repo_path),
            "is_git": is_git,
            "default_branch": default_branch,
            "languages": languages,
            "frameworks": frameworks,
            "file_count": file_count,
            "total_size_bytes": total_size,
            "top_dependencies": top_deps
        }

    def _detect_frameworks(self) -> Tuple[List[str], List[str]]:
        """Inspect package manifest files to detect frameworks and key dependencies."""
        frameworks: Set[str] = set()
        top_deps: List[str] = []

        # Check Python dependencies
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip().lower()
                        if not line or line.startswith("#"):
                            continue
                        dep_name = re.split(r"[=<>~;]", line)[0].strip()
                        top_deps.append(dep_name)
                        if "fastapi" in dep_name:
                            frameworks.add("FastAPI")
                        elif "flask" in dep_name:
                            frameworks.add("Flask")
                        elif "django" in dep_name:
                            frameworks.add("Django")
                        elif "sqlalchemy" in dep_name:
                            frameworks.add("SQLAlchemy")
                        elif "pytest" in dep_name:
                            frameworks.add("Pytest")
            except Exception:
                pass

        # Check Node.js / JavaScript / TypeScript dependencies
        pkg_file = self.repo_path / "package.json"
        if pkg_file.exists():
            try:
                import json
                with open(pkg_file, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    for dep in deps.keys():
                        top_deps.append(dep)
                        dep_lower = dep.lower()
                        if "react" in dep_lower:
                            frameworks.add("React")
                        elif "vite" in dep_lower:
                            frameworks.add("Vite")
                        elif "next" in dep_lower:
                            frameworks.add("Next.js")
                        elif "vue" in dep_lower:
                            frameworks.add("Vue")
                        elif "tailwindcss" in dep_lower:
                            frameworks.add("Tailwind CSS")
                        elif "express" in dep_lower:
                            frameworks.add("Express")
                        elif "vitest" in dep_lower:
                            frameworks.add("Vitest")
            except Exception:
                pass

        return sorted(list(frameworks)), sorted(list(set(top_deps)))[:20]

    def build_file_tree(self, max_depth: int = 5) -> FileTreeNode:
        """Construct hierarchical file tree for visualization."""
        def _walk_tree(current_path: Path, current_depth: int) -> Optional[FileTreeNode]:
            if current_depth > max_depth or self.is_file_ignored(current_path):
                return None

            if current_path.is_file():
                try:
                    size = current_path.stat().st_size
                except OSError:
                    size = 0
                ext = current_path.suffix.lower()
                lang = EXTENSION_LANGUAGE_MAP.get(ext, "Text")
                return FileTreeNode(
                    name=current_path.name,
                    path=str(current_path.relative_to(self.repo_path)),
                    type="file",
                    size_bytes=size,
                    language=lang
                )

            # Directory
            children: List[FileTreeNode] = []
            try:
                entries = sorted(list(current_path.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
                for entry in entries:
                    child_node = _walk_tree(entry, current_depth + 1)
                    if child_node:
                        children.append(child_node)
            except (PermissionError, OSError):
                pass

            return FileTreeNode(
                name=current_path.name if current_path != self.repo_path else self.repo_path.name,
                path=str(current_path.relative_to(self.repo_path)) if current_path != self.repo_path else ".",
                type="directory",
                children=children
            )

        root_node = _walk_tree(self.repo_path, 0)
        return root_node or FileTreeNode(name=self.repo_path.name, path=".", type="directory", children=[])

    def read_safe_file(self, relative_path: str, max_chars: int = 100000) -> Dict[str, Any]:
        """Safely inspect file contents, enforcing canonical bounds and secret protections."""
        target_path = (self.repo_path / relative_path).resolve()
        # Verify no directory traversal outside repo_path
        if target_path != self.repo_path and self.repo_path not in target_path.parents:
            raise SecurityException(f"Path traversal attempted: {relative_path}")

        if self.is_file_ignored(target_path):
            raise SecurityException(f"File '{relative_path}' is protected and cannot be inspected.")

        if not target_path.is_file():
            raise SecurityException(f"File not found: {relative_path}")

        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars + 1)
        except Exception as e:
            raise SecurityException(f"Failed to read file '{relative_path}': {str(e)}")

        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars]

        line_count = content.count("\n") + 1
        ext = target_path.suffix.lower()
        lang = EXTENSION_LANGUAGE_MAP.get(ext, "Text")

        return {
            "file_path": str(target_path),
            "relative_path": relative_path,
            "language": lang,
            "line_count": line_count,
            "size_bytes": target_path.stat().st_size,
            "content": content,
            "truncated": truncated
        }

    def extract_symbols(self, relative_path: str) -> List[SymbolItem]:
        """Extract functions, classes, async definitions, interfaces using AST or pattern matching."""
        target_path = (self.repo_path / relative_path).resolve()
        if self.is_file_ignored(target_path) or not target_path.is_file():
            return []

        symbols: List[SymbolItem] = []
        ext = target_path.suffix.lower()

        try:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except Exception:
            return []

        if ext == ".py":
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        doc = ast.get_docstring(node)
                        symbols.append(SymbolItem(
                            name=node.name,
                            kind="function",
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                            docstring=doc
                        ))
                    elif isinstance(node, ast.AsyncFunctionDef):
                        doc = ast.get_docstring(node)
                        symbols.append(SymbolItem(
                            name=node.name,
                            kind="async_def",
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                            docstring=doc
                        ))
                    elif isinstance(node, ast.ClassDef):
                        doc = ast.get_docstring(node)
                        symbols.append(SymbolItem(
                            name=node.name,
                            kind="class",
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                            docstring=doc
                        ))
            except Exception:
                pass
        elif ext in [".ts", ".tsx", ".js", ".jsx"]:
            # Pattern extraction for TS/JS
            lines = source.split("\n")
            func_pat = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)")
            arrow_pat = re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(")
            class_pat = re.compile(r"^\s*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)")
            iface_pat = re.compile(r"^\s*(?:export\s+)?interface\s+([a-zA-Z0-9_$]+)")

            for idx, line in enumerate(lines, 1):
                f_match = func_pat.match(line)
                if f_match:
                    symbols.append(SymbolItem(name=f_match.group(1), kind="function", line_start=idx, line_end=idx))
                    continue
                a_match = arrow_pat.match(line)
                if a_match:
                    symbols.append(SymbolItem(name=a_match.group(1), kind="function", line_start=idx, line_end=idx))
                    continue
                c_match = class_pat.match(line)
                if c_match:
                    symbols.append(SymbolItem(name=c_match.group(1), kind="class", line_start=idx, line_end=idx))
                    continue
                i_match = iface_pat.match(line)
                if i_match:
                    symbols.append(SymbolItem(name=i_match.group(1), kind="interface", line_start=idx, line_end=idx))

        return symbols

    def search_code(self, query: str, max_results: int = 50) -> List[SearchResultItem]:
        """Search safe source files for query string or regex."""
        results: List[SearchResultItem] = []
        total_matches = 0

        try:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
        except Exception:
            return []

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORED_DIRS and not self.is_file_ignored(Path(root) / d)]
            for file in files:
                fpath = Path(root) / file
                if self.is_file_ignored(fpath):
                    continue

                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        file_matches: List[SearchMatch] = []
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                file_matches.append(SearchMatch(
                                    line_number=line_num,
                                    line_text=line.strip()[:200]
                                ))
                                total_matches += 1
                                if total_matches >= max_results:
                                    break

                        if file_matches:
                            rel = str(fpath.relative_to(self.repo_path))
                            ext = fpath.suffix.lower()
                            results.append(SearchResultItem(
                                file_path=str(fpath),
                                relative_path=rel,
                                language=EXTENSION_LANGUAGE_MAP.get(ext, "Text"),
                                matches=file_matches
                            ))
                            if total_matches >= max_results:
                                return results
                except Exception:
                    continue

        return results

    def retrieve_context(
        self,
        prompt: str,
        max_tokens: int = 8000,
        max_files: int = 10
    ) -> List[RelevantFileContext]:
        """
        Rank repository files by relevance to prompt, budget tokens, and return context payloads.
        """
        # Tokenize prompt words, strip punctuation
        raw_words = re.findall(r"[a-zA-Z0-9_]{3,}", prompt.lower())
        stopwords = {"this", "that", "with", "from", "have", "what", "which", "will", "make", "test", "file", "please", "help"}
        keywords = [w for w in raw_words if w not in stopwords]

        scored_files: List[Tuple[float, str, Path, str]] = []

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORED_DIRS and not self.is_file_ignored(Path(root) / d)]
            for file in files:
                fpath = Path(root) / file
                if self.is_file_ignored(fpath):
                    continue

                rel_str = str(fpath.relative_to(self.repo_path)).lower()
                score = 0.0
                reasons: List[str] = []

                # 1. Match in file name / path
                for kw in keywords:
                    if kw in rel_str:
                        score += 5.0
                        reasons.append(f"Filename matches '{kw}'")

                # 2. Inspect file content & symbols
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(50000)  # read first 50KB for scoring
                        content_lower = content.lower()
                        for kw in keywords:
                            count = content_lower.count(kw)
                            if count > 0:
                                score += min(count, 5) * 1.0
                                reasons.append(f"Content mentions '{kw}' ({count}x)")
                except Exception:
                    continue

                if score > 0:
                    scored_files.append((score, "; ".join(reasons[:3]), fpath, content))

        # Sort by highest relevance score
        scored_files.sort(key=lambda x: x[0], reverse=True)

        selected: List[RelevantFileContext] = []
        tokens_used = 0

        for score, reason, fpath, content in scored_files[:max_files]:
            rel = str(fpath.relative_to(self.repo_path))
            # Rough token estimate: 4 chars per token
            est_tokens = len(content) // 4
            if tokens_used + est_tokens > max_tokens and selected:
                # Truncate content to fit remaining budget
                remaining_tokens = max_tokens - tokens_used
                if remaining_tokens > 200:
                    truncated_chars = remaining_tokens * 4
                    content = content[:truncated_chars] + "\n...[truncated for context budget]..."
                    est_tokens = remaining_tokens
                else:
                    break

            tokens_used += est_tokens
            ext = fpath.suffix.lower()
            selected.append(RelevantFileContext(
                file_path=str(fpath),
                relative_path=rel,
                language=EXTENSION_LANGUAGE_MAP.get(ext, "Text"),
                relevance_score=round(score, 2),
                relevance_reason=reason,
                content=content,
                token_estimate=est_tokens
            ))

        return selected

    def list_repo_files(self) -> List[str]:
        """Return list of all non-ignored relative file paths in repository."""
        file_list = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORED_DIRS and not self.is_file_ignored(Path(root) / d)]
            for f in files:
                fpath = Path(root) / f
                if not self.is_file_ignored(fpath) and fpath.is_file():
                    file_list.append(str(fpath.relative_to(self.repo_path)))
        return sorted(file_list)

    def build_dependency_graph(self) -> DependencyGraphResponse:
        """Extract imports from Python and JS/TS files to construct a directed dependency graph."""
        all_files = self.list_repo_files()
        edges: List[Dict[str, str]] = []
        dep_counts: Dict[str, int] = {f: 0 for f in all_files}
        connected_nodes: Set[str] = set()

        for rel_file in all_files:
            fpath = self.repo_path / rel_file
            ext = fpath.suffix.lower()
            imported_files: Set[str] = set()

            if ext == ".py":
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                resolved = self._resolve_python_import(alias.name, rel_file, all_files)
                                if resolved:
                                    imported_files.add(resolved)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                resolved = self._resolve_python_import(node.module, rel_file, all_files)
                                if resolved:
                                    imported_files.add(resolved)
                except Exception:
                    pass
            elif ext in [".ts", ".tsx", ".js", ".jsx"]:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    import_matches = re.findall(r"(?:from|require\()\s*['\"]([^'\"]+)['\"]", content)
                    for imp in import_matches:
                        resolved = self._resolve_js_import(imp, rel_file, all_files)
                        if resolved:
                            imported_files.add(resolved)
                except Exception:
                    pass

            for imp in imported_files:
                if imp != rel_file:
                    edges.append({"source": rel_file, "target": imp})
                    dep_counts[imp] = dep_counts.get(imp, 0) + 1
                    connected_nodes.add(rel_file)
                    connected_nodes.add(imp)

        isolated = [f for f in all_files if f not in connected_nodes]

        return DependencyGraphResponse(
            nodes=all_files,
            edges=edges,
            dependency_counts=dep_counts,
            isolated_files=isolated
        )

    def _resolve_python_import(self, module_name: str, current_file: str, all_files: List[str]) -> Optional[str]:
        candidates = [
            module_name.replace(".", "/") + ".py",
            module_name.replace(".", "/") + "/__init__.py",
        ]
        cur_dir = str(Path(current_file).parent)
        if cur_dir != ".":
            candidates.append(f"{cur_dir}/{module_name.replace('.', '/')}.py")

        for cand in candidates:
            cand_str = cand.lstrip("./")
            if cand_str in all_files:
                return cand_str

        base_name = module_name.split(".")[-1] + ".py"
        for f in all_files:
            if Path(f).name == base_name:
                return f

        return None

    def _resolve_js_import(self, import_path: str, current_file: str, all_files: List[str]) -> Optional[str]:
        if not import_path.startswith("."):
            return None
        cur_dir = Path(current_file).parent
        resolved = (cur_dir / import_path).resolve()
        try:
            rel = str(resolved.relative_to(self.repo_path))
        except ValueError:
            return None

        for ext in ["", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js"]:
            cand = rel + ext
            if cand in all_files:
                return cand
        return None

    def discover_cross_file_symbols(self) -> List[CrossFileSymbolMap]:
        """Discovers all defined symbols across the codebase and maps them to cross-file call sites."""
        all_files = self.list_repo_files()
        defined_symbols: List[Dict[str, Any]] = []

        for rel_file in all_files:
            symbols = self.extract_symbols(rel_file)
            for s in symbols:
                if len(s.name) >= 3 and not s.name.startswith("__"):
                    defined_symbols.append({
                        "name": s.name,
                        "file": rel_file,
                        "kind": s.kind,
                        "line": s.line_start,
                        "docstring": s.docstring
                    })

        results: List[CrossFileSymbolMap] = []
        for sym in defined_symbols[:100]:
            call_sites = self.locate_call_sites(sym["name"], exclude_file=sym["file"])
            results.append(CrossFileSymbolMap(
                symbol_name=sym["name"],
                defining_file=sym["file"],
                kind=sym["kind"],
                line=sym["line"],
                docstring=sym["docstring"],
                call_sites=call_sites
            ))

        return results

    def locate_call_sites(self, symbol_name: str, exclude_file: Optional[str] = None) -> List[CallSiteItem]:
        """Find where symbol_name is referenced or invoked across files."""
        call_sites = []
        all_files = self.list_repo_files()
        call_pattern = re.compile(rf"\b{re.escape(symbol_name)}\b")

        for rel_file in all_files:
            if exclude_file and rel_file == exclude_file:
                continue

            fpath = self.repo_path / rel_file
            if fpath.suffix.lower() not in EXTENSION_LANGUAGE_MAP:
                continue

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, start=1):
                        if call_pattern.search(line):
                            call_sites.append(CallSiteItem(
                                calling_file=rel_file,
                                line_number=line_no,
                                line_text=line.strip()[:150],
                                callee_symbol=symbol_name
                            ))
                            if len(call_sites) >= 20:
                                return call_sites
            except Exception:
                continue

        return call_sites

    def identify_test_files(self, target_file: str) -> List[str]:
        """Identify candidate test files covering the target_file."""
        all_files = self.list_repo_files()
        stem = Path(target_file).stem
        candidates = []

        patterns = [
            f"test_{stem}.py",
            f"{stem}_test.py",
            f"test_{stem}.ts",
            f"{stem}.test.ts",
            f"{stem}.test.tsx",
            f"{stem}.spec.ts",
            f"test_{stem}.js"
        ]

        for f in all_files:
            f_name = Path(f).name
            if f_name in patterns or f"test_{stem}" in f.lower() or f"{stem}_test" in f.lower():
                candidates.append(f)

        return candidates

    def analyze_change_impact(self, target_file: str) -> ChangeImpactReport:
        """Calculates blast radius and regression risk of modifying target_file."""
        dep_graph = self.build_dependency_graph()
        direct_impacted: Set[str] = set()
        transitive_impacted: Set[str] = set()

        for edge in dep_graph.edges:
            if edge["target"] == target_file:
                direct_impacted.add(edge["source"])

        visited = set(direct_impacted)
        queue = list(direct_impacted)
        while queue:
            curr = queue.pop(0)
            for edge in dep_graph.edges:
                if edge["target"] == curr and edge["source"] not in visited:
                    visited.add(edge["source"])
                    transitive_impacted.add(edge["source"])
                    queue.append(edge["source"])

        test_files = self.identify_test_files(target_file)
        for imp in direct_impacted:
            test_files.extend(self.identify_test_files(imp))
        test_files = sorted(list(set(test_files)))

        total_impact = len(direct_impacted) + len(transitive_impacted)
        if total_impact > 5 or "auth" in target_file or "security" in target_file or "database" in target_file:
            risk = "HIGH"
        elif total_impact > 0:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        summary = (
            f"Modifying '{target_file}' directly impacts {len(direct_impacted)} file(s) and "
            f"{len(transitive_impacted)} transitive file(s). Found {len(test_files)} relevant test file(s). Risk: {risk}."
        )

        return ChangeImpactReport(
            target_file=target_file,
            directly_impacted_files=sorted(list(direct_impacted)),
            transitively_impacted_files=sorted(list(transitive_impacted)),
            associated_test_files=test_files,
            risk_level=risk,
            summary=summary
        )
