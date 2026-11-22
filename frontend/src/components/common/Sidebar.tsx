import React from 'react';
import {
  LayoutDashboard,
  Code2,
  FolderGit2,
  FileCode2,
  Terminal,
  ListTree,
  GitCompare,
  FlaskConical,
  BarChart3,
  Settings,
  Cpu,
  HelpCircle
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  activeWorkspaceName?: string;
  onOpenTour?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, activeWorkspaceName, onOpenTour }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'workspace-ide', label: 'Engineering IDE', icon: Code2 },
    { id: 'workspaces', label: 'Workspaces', icon: FolderGit2 },
    { id: 'repo-explorer', label: 'Repo Explorer', icon: FileCode2 },
    { id: 'task-console', label: 'AI Task Console', icon: Terminal },
    { id: 'planning', label: 'Planning Engine', icon: ListTree },
    { id: 'diff-review', label: 'Diff Review', icon: GitCompare },
    { id: 'test-results', label: 'Test & Verification', icon: FlaskConical },
    { id: 'evaluation', label: 'Evaluation Lab', icon: BarChart3 },
    { id: 'settings', label: 'System Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-navy-900 border-r border-navy-800 flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-navy-800">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wider text-slate-100 flex items-center space-x-1.5 font-mono">
              <span>AETHER</span>
              <span className="text-cyan-400">ENGINEER</span>
            </h1>
            <p className="text-[11px] text-slate-400 font-mono">Autonomous AI SWE Platform</p>
          </div>
        </div>
      </div>

      {/* Workspace Indicator */}
      <div className="px-4 py-3 bg-navy-950/60 border-b border-navy-800/80">
        <p className="text-[10px] uppercase font-mono tracking-wider text-slate-400">Active Workspace</p>
        <p className="text-xs font-medium text-slate-200 truncate mt-0.5">
          {activeWorkspaceName || 'No Workspace Selected'}
        </p>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-navy-800/60 border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Interactive Tour CTA */}
      {onOpenTour && (
        <div className="px-3 py-2 border-t border-navy-800/60">
          <button
            onClick={onOpenTour}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg bg-navy-800 hover:bg-navy-700/80 border border-cyan-500/20 text-cyan-300 text-xs font-medium transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span>Product Tour</span>
          </button>
        </div>
      )}

      {/* Footer Info */}
      <div className="p-3 border-t border-navy-800 text-[11px] font-mono text-slate-400 flex items-center justify-between">
        <span className="flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>Mac M1 (8GB)</span>
        </span>
        <span className="text-slate-400">v0.1.0</span>
      </div>
    </aside>
  );
};

