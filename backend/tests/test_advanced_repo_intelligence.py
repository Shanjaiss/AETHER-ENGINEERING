import shutil
import pytest
from pathlib import Path
from backend.app.core.config import settings
from backend.app.services.repo_intelligence.scanner import RepositoryScanner

@pytest.fixture
def advanced_repo():
    repo_dir = settings.resolved_workspace_root / "advanced_intelligence_fixture"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Module A (auth.py)
    (repo_dir / "auth.py").write_text("def authenticate(token: str) -> bool:\n    return len(token) > 0\n")

    # Module B (service.py imports auth)
    (repo_dir / "service.py").write_text("import auth\ndef login_user(token: str):\n    return auth.authenticate(token)\n")

    # Module C (app.py imports service)
    (repo_dir / "app.py").write_text("import service\ndef handle_request(req: dict):\n    return service.login_user(req.get('token', ''))\n")

    # Test file (test_auth.py)
    (repo_dir / "test_auth.py").write_text("import auth\ndef test_auth():\n    assert auth.authenticate('valid') is True\n")

    yield repo_dir

    if repo_dir.exists():
        shutil.rmtree(repo_dir)

def test_dependency_graph_and_impact_analysis(advanced_repo):
    scanner = RepositoryScanner(advanced_repo)

    # 1. Dependency Graph
    dep_graph = scanner.build_dependency_graph()
    assert len(dep_graph.nodes) >= 4
    edge_pairs = [(e["source"], e["target"]) for e in dep_graph.edges]
    assert ("service.py", "auth.py") in edge_pairs
    assert ("app.py", "service.py") in edge_pairs
    assert ("test_auth.py", "auth.py") in edge_pairs

    # 2. Call-Site Locator
    call_sites = scanner.locate_call_sites("authenticate", exclude_file="auth.py")
    assert len(call_sites) >= 2
    calling_files = {cs.calling_file for cs in call_sites}
    assert "service.py" in calling_files
    assert "test_auth.py" in calling_files

    # 3. Test File Identification
    test_files = scanner.identify_test_files("auth.py")
    assert "test_auth.py" in test_files

    # 4. Change Impact Analysis
    impact = scanner.analyze_change_impact("auth.py")
    assert "service.py" in impact.directly_impacted_files
    assert "app.py" in impact.transitively_impacted_files
    assert "test_auth.py" in impact.associated_test_files
    assert impact.risk_level in ["MEDIUM", "HIGH"]
    assert "directly impacts" in impact.summary

def test_cross_file_symbol_discovery():
    repo_dir = settings.resolved_workspace_root / "symbol_discovery_fixture"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)

    try:
        (repo_dir / "models.py").write_text("class UserProfile:\n    def __init__(self, name: str):\n        self.name = name\n")
        (repo_dir / "views.py").write_text("from models import UserProfile\ndef render_user():\n    u = UserProfile('Alice')\n    return u.name\n")

        scanner = RepositoryScanner(repo_dir)
        symbols = scanner.discover_cross_file_symbols()

        user_profile_sym = next((s for s in symbols if s.symbol_name == "UserProfile"), None)
        assert user_profile_sym is not None
        assert user_profile_sym.defining_file == "models.py"
        assert user_profile_sym.kind == "class"
        assert len(user_profile_sym.call_sites) >= 1
        assert user_profile_sym.call_sites[0].calling_file == "views.py"
    finally:
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
