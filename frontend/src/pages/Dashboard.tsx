import React from 'react';
import {
  FolderGit2,
  Terminal,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Plus,
  Play,
  Cpu
} from 'lucide-react';
import { Workspace, Task, HealthResponse } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';

interface DashboardProps {
  health?: HealthResponse;
  workspaces: Workspace[];
  tasks: Task[];
  onNavigate: (tab: string) => void;
  activeWorkspace?: Workspace;
}

export const Dashboard: React.FC<DashboardProps> = ({
  health,
  workspaces,
  tasks,
  onNavigate,
  activeWorkspace,
}) => {
  const completedTasks = tasks.filter((t) => t.status === 'COMPLETED').length;
  const inProgressTasks = tasks.filter((t) =>
    ['PLANNING', 'CODING', 'VERIFYING', 'DEBUGGING', 'ANALYZING'].includes(t.status)
  ).length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Welcome & Tagline */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 font-mono tracking-tight flex items-center space-x-2">
            <span>AETHER ENGINEER</span>
            <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              v{health?.version || '0.1.0'}
            </span>
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Autonomous AI Software Engineering Platform — <span className="text-cyan-400 italic">From Requirement to Verified Code</span>.
          </p>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={() => onNavigate('workspaces')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 border border-navy-700 text-slate-200 text-xs font-mono transition"
          >
            <FolderGit2 className="w-4 h-4 text-cyan-400" />
            <span>Manage Workspaces</span>
          </button>
          <button
            onClick={() => onNavigate('task-console')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-medium transition shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>New AI Engineering Task</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono">
        <div className="bg-navy-900 border border-navy-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Workspaces</span>
            <FolderGit2 className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{workspaces.length}</p>
          <p className="text-[11px] text-slate-400 mt-1">Permitted local roots</p>
        </div>

        <div className="bg-navy-900 border border-navy-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Tasks</span>
            <Terminal className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{tasks.length}</p>
          <p className="text-[11px] text-slate-400 mt-1">{inProgressTasks} running / {completedTasks} verified</p>
        </div>

        <div className="bg-navy-900 border border-navy-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Execution Sandbox</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-sm font-semibold text-emerald-400 mt-2">Isolated Copies Only</p>
          <p className="text-[11px] text-slate-400 mt-1">Zero direct source edits</p>
        </div>

        <div className="bg-navy-900 border border-navy-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Host Environment</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-sm font-semibold text-slate-200 mt-2">Apple M1 (8GB Unified)</p>
          <p className="text-[11px] text-slate-400 mt-1">Low memory footprint mode</p>
        </div>
      </div>

      {/* Active Workspace Banner */}
      {activeWorkspace ? (
        <div className="bg-navy-900/90 border border-cyan-500/20 rounded-xl p-5 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[11px] uppercase font-mono text-cyan-400 tracking-wider">Current Target Repository</span>
            <h3 className="text-lg font-semibold text-slate-100 font-mono">{activeWorkspace.name}</h3>
            <p className="text-xs text-slate-400 font-mono">{activeWorkspace.path}</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onNavigate('repo-explorer')}
              className="px-3 py-1.5 rounded bg-navy-800 hover:bg-navy-700 text-slate-200 text-xs font-mono border border-navy-700"
            >
              Explore Codebase
            </button>
            <button
              onClick={() => onNavigate('task-console')}
              className="px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-medium"
            >
              Start Task
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-6 text-center space-y-3">
          <FolderGit2 className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-base font-medium text-slate-200">No Workspace Selected</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Import an authorized local Git repository or project to analyze the architecture and execute AI engineering workflows.
          </p>
          <button
            onClick={() => onNavigate('workspaces')}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-medium"
          >
            Import Workspace
          </button>
        </div>
      )}

      {/* Recent Activity Table */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 font-mono uppercase tracking-wider">
            Recent Engineering Tasks
          </h3>
          <button
            onClick={() => onNavigate('task-console')}
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 font-mono"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {tasks.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs font-mono">
            No engineering tasks have been launched yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-navy-800 text-slate-400">
                  <th className="pb-3 font-medium">Task Title</th>
                  <th className="pb-3 font-medium">Phase</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Repairs</th>
                  <th className="pb-3 font-medium text-right">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/60">
                {tasks.slice(0, 5).map((task) => (
                  <tr key={task.id} className="hover:bg-navy-850/50 cursor-pointer" onClick={() => onNavigate('task-console')}>
                    <td className="py-3 font-medium text-slate-200">{task.title}</td>
                    <td className="py-3 text-slate-400">{task.current_phase}</td>
                    <td className="py-3"><StatusBadge status={task.status} size="sm" /></td>
                    <td className="py-3 text-slate-400">{task.repair_attempts}</td>
                    <td className="py-3 text-right text-slate-400">
                      {new Date(task.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

