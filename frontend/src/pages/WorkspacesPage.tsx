import React, { useState } from 'react';
import { FolderGit2, Plus, Trash2, Check, AlertTriangle, ShieldCheck } from 'lucide-react';
import { Workspace } from '../types';
import { api } from '../services/api';

interface WorkspacesPageProps {
  workspaces: Workspace[];
  activeWorkspace?: Workspace;
  onSelectWorkspace: (ws: Workspace) => void;
  onRefresh: () => void;
}

export const WorkspacesPage: React.FC<WorkspacesPageProps> = ({
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  onRefresh,
}) => {
  const [name, setName] = useState('');
  const [path, setPath] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !path.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const created = await api.createWorkspace({ name: name.trim(), path: path.trim() });
      setName('');
      setPath('');
      onRefresh();
      onSelectWorkspace(created);
    } catch (err: any) {
      setError(err.message || 'Failed to create workspace');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to remove this workspace? Original files remain untouched.')) return;
    try {
      await api.deleteWorkspace(id);
      onRefresh();
    } catch (err: any) {
      alert(`Error deleting workspace: ${err.message}`);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 font-mono">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <FolderGit2 className="w-5 h-5 text-cyan-400" />
          <span>Workspaces & Repositories</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Manage authorized development roots and local Git repositories. Security rules prevent access outside permitted folders.
        </p>
      </div>

      {/* Import Form */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <Plus className="w-4 h-4 text-cyan-400" />
          <span>Import Local Repository</span>
        </h3>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-400 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Workspace Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. My Fastapi App"
              required
              className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs text-slate-400 mb-1">Local Absolute Path</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder="/Users/shanjaisenthil/Documents/..."
                required
                className="flex-1 bg-navy-950 border border-navy-700 rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
              />
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-semibold transition"
              >
                {isSubmitting ? 'Importing...' : 'Register'}
              </button>
            </div>
          </div>
        </form>

        <div className="flex items-center space-x-2 text-[11px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>Enforces canonical path resolution and directory traversal protections.</span>
        </div>
      </div>

      {/* Workspaces List */}
      <div className="space-y-3">
        <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
          Registered Workspaces ({workspaces.length})
        </h3>

        {workspaces.length === 0 ? (
          <div className="bg-navy-900 border border-navy-800 rounded-xl p-8 text-center text-xs text-slate-400">
            No workspaces registered yet. Add a workspace above to get started.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {workspaces.map((ws) => {
              const isSelected = activeWorkspace?.id === ws.id;
              return (
                <div
                  key={ws.id}
                  onClick={() => onSelectWorkspace(ws)}
                  className={`bg-navy-900 border rounded-xl p-4 cursor-pointer transition flex items-center justify-between ${
                    isSelected
                      ? 'border-cyan-500 bg-navy-850 shadow-sm'
                      : 'border-navy-800 hover:border-navy-700'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-3">
                      <span className="font-semibold text-sm text-slate-100">{ws.name}</span>
                      {isSelected && (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center space-x-1">
                          <Check className="w-3 h-3" />
                          <span>Active</span>
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 truncate max-w-xl">{ws.path}</p>
                  </div>

                  <div className="flex items-center space-x-4">
                    <span className="text-[11px] text-slate-400">
                      Added {new Date(ws.created_at).toLocaleDateString()}
                    </span>
                    <button
                      onClick={(e) => handleDelete(ws.id, e)}
                      className="p-1.5 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition"
                      title="Remove workspace"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

