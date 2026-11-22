from pathlib import Path
from backend.app.core.config import settings

def test_create_and_list_workspace(client, tmp_path):
    # Configure tmp_path as an allowed root for testing
    workspace_dir = settings.resolved_workspace_root / "test_project"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "name": "Test Project",
        "path": str(workspace_dir),
        "metadata_json": {"env": "test"}
    }
    create_res = client.post("/api/v1/workspaces/", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["name"] == "Test Project"
    assert "id" in created_data

    list_res = client.get("/api/v1/workspaces/")
    assert list_res.status_code == 200
    workspaces = list_res.json()
    assert len(workspaces) == 1
    assert workspaces[0]["id"] == created_data["id"]

def test_workspace_security_directory_traversal_blocked(client):
    # Try unauthorized path /etc
    payload = {
        "name": "Malicious Workspace",
        "path": "/etc"
    }
    res = client.post("/api/v1/workspaces/", json=payload)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_create_task_and_cancel(client):
    workspace_dir = settings.resolved_workspace_root / "task_project"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Task Test WS",
        "path": str(workspace_dir)
    })
    ws_id = ws_res.json()["id"]

    task_res = client.post("/api/v1/tasks/", json={
        "workspace_id": ws_id,
        "title": "Fix memory leak",
        "description": "Locate and fix memory leak in caching layer"
    })
    assert task_res.status_code == 201
    task_data = task_res.json()
    task_id = task_data["id"]
    assert task_data["status"] == "PENDING"

    # Cancel task
    cancel_res = client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

