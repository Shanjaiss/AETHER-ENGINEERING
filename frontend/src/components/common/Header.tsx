import React from 'react';
import { ShieldCheck, Server, Sparkles, AlertCircle } from 'lucide-react';
import { HealthResponse, Workspace } from '../../types';

interface HeaderProps {
  health?: HealthResponse;
  workspaces: Workspace[];
  activeWorkspace?: Workspace;
  onSelectWorkspace: (ws: Workspace) => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
}) => {
  return (
    <header className="h-14 bg-navy-900 border-b border-navy-800 px-6 flex items-center justify-between">
      {/* Left: Workspace dropdown */}
      <div className="flex items-center space-x-3">
        <span className="text-xs text-slate-400 font-mono">Workspace:</span>
        <select
          value={activeWorkspace?.id || ''}
          onChange={(e) => {
            const found = workspaces.find((w) => w.id === e.target.value);
            if (found) onSelectWorkspace(found);
          }}
          className="bg-navy-950 border border-navy-700 text-xs text-slate-200 rounded px-2.5 py-1 focus:outline-none focus:border-cyan-500 font-mono"
        >
          <option value="" disabled>Select Workspace...</option>
          {workspaces.map((w) => (
            <option key={w.id} value={w.id}>{w.name} ({w.path})</option>
          ))}
        </select>
      </div>

      {/* Right: Badges */}
      <div className="flex items-center space-x-3 text-xs font-mono">
        {/* Isolated Sandbox Badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-navy-950 border border-navy-700 text-slate-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>Isolated Workspaces</span>
        </div>

        {/* Database / Backend Status */}
        <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border ${
          health?.database_connected
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
        }`}>
          <Server className="w-3.5 h-3.5" />
          <span>{health?.database_connected ? 'DB Connected' : 'DB Offline'}</span>
        </div>

        {/* LLM Status */}
        <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border ${
          health?.llm_configured
            ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
            : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
        }`}>
          {health?.llm_configured ? (
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span>
            {health?.llm_configured
              ? `AI: ${health.llm_provider}`
              : 'AI: Unconfigured'}
          </span>
        </div>
      </div>
    </header>
  );
};

