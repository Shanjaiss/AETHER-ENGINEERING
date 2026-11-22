import pytest
from pathlib import Path
from backend.app.core.config import settings

@pytest.fixture
def sample_repo(tmp_path):
    repo_dir = settings.resolved_workspace_root / "sample_codebase"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a Python file with functions, classes, and async functions
    auth_py = repo_dir / "auth.py"
    auth_py.write_text("""\"\"\"Authentication module.\"\"\"

def authenticate_user(username: str, token: str) -> bool:
    \"\"\"Validate user credentials against token.\"\"\"
    return token == "valid_token"

async def async_refresh_jwt(token: str) -> str:
    \"\"\"Asynchronously refresh expired JWT token.\"\"\"
    return "new_jwt_token"

class AuthHandler:
    \"\"\"Core security and token handler.\"\"\"
    def verify_role(self, user_role: str) -> bool:
        return user_role == "admin"
""")

    # 2. Create TypeScript file
    utils_ts = repo_dir / "utils.ts"
    utils_ts.write_text("""export interface UserSession {
  userId: string;
  expiresAt: number;
}

export function parseSessionToken(raw: string): UserSession {
  return { userId: "user-1", expiresAt: Date.now() + 3600 };
}
""")

    # 3. Create manifest files
    req_txt = repo_dir / "requirements.txt"
    req_txt.write_text("fastapi>=0.110.0\npytest>=8.0.0\n")

    pkg_json = repo_dir / "package.json"
    pkg_json.write_text('{"dependencies": {"react": "^18.3.0"}, "devDependencies": {"vite": "^5.0.0"}}')

    # 4. Create gitignore and ignored file
    gitignore = repo_dir / ".gitignore"
    gitignore.write_text("ignored_folder/\n*.secret.txt\n")

    ignored_dir = repo_dir / "ignored_folder"
    ignored_dir.mkdir(exist_ok=True)
    (ignored_dir / "temp.txt").write_text("should be ignored")

    (repo_dir / "test.secret.txt").write_text("secret stuff")

    # 5. Create sensitive files that must be BLOCKED by security
    (repo_dir / ".env").write_text("SECRET_KEY=supersecret123\nDATABASE_URL=sqlite:///db.sqlite\n")
    (repo_dir / "server.key").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...")

    return repo_dir

def test_repo_scan_and_security(client, sample_repo):
    # 1. Register workspace
    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Sample Codebase Workspace",
        "path": str(sample_repo)
    })
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # 2. Scan repository
    scan_res = client.post("/api/v1/repositories/scan", json={
        "workspace_id": ws_id,
        "path": str(sample_repo)
    })
    assert scan_res.status_code == 200
    repo_data = scan_res.json()
    repo_id = repo_data["id"]

    # Verify technologies detected
    assert "FastAPI" in repo_data["frameworks"]
    assert "React" in repo_data["frameworks"]
    assert "Pytest" in repo_data["frameworks"]
    assert "Vite" in repo_data["frameworks"]
    assert "Python" in repo_data["languages"]
    assert "TypeScript" in repo_data["languages"]

    # 3. Verify file tree omits ignored and forbidden files
    tree_res = client.get(f"/api/v1/repositories/{repo_id}/tree")
    assert tree_res.status_code == 200
    tree_data = tree_res.json()
    file_names = [child["name"] for child in tree_data.get("children", [])]

    assert "auth.py" in file_names
    assert "utils.ts" in file_names
    # MUST NOT contain sensitive or ignored files
    assert ".env" not in file_names
    assert "server.key" not in file_names
    assert "ignored_folder" not in file_names
    assert "test.secret.txt" not in file_names

    # 4. Safe file content inspection
    file_res = client.get(f"/api/v1/repositories/{repo_id}/file?path=auth.py")
    assert file_res.status_code == 200
    assert "authenticate_user" in file_res.json()["content"]

    # 5. Security: Direct attempt to read .env MUST be blocked
    env_res = client.get(f"/api/v1/repositories/{repo_id}/file?path=.env")
    assert env_res.status_code == 403

    # 6. Security: Path traversal attempt MUST be blocked
    traversal_res = client.get(f"/api/v1/repositories/{repo_id}/file?path=../../etc/passwd")
    assert traversal_res.status_code == 403

    # 7. AST Symbol extraction
    sym_res = client.get(f"/api/v1/repositories/{repo_id}/symbols?path=auth.py")
    assert sym_res.status_code == 200
    symbols = sym_res.json()["symbols"]
    sym_names = [s["name"] for s in symbols]
    assert "authenticate_user" in sym_names
    assert "async_refresh_jwt" in sym_names
    assert "AuthHandler" in sym_names

    # 8. Code search
    search_res = client.post(f"/api/v1/repositories/{repo_id}/search", json={
        "query": "authenticate_user",
        "max_results": 10
    })
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_matches"] >= 1
    assert search_data["results"][0]["relative_path"] == "auth.py"

    # 9. Context retrieval & ranking
    ctx_res = client.post(f"/api/v1/repositories/{repo_id}/context", json={
        "prompt": "We need to fix the expired token handling in authenticate_user and JWT refresh",
        "max_tokens": 4000,
        "max_files": 5
    })
    assert ctx_res.status_code == 200
    ctx_data = ctx_res.json()
    assert ctx_data["total_files_ranked"] >= 1
    top_file = ctx_data["selected_files"][0]
    assert top_file["relative_path"] == "auth.py"
    assert top_file["relevance_score"] > 0

