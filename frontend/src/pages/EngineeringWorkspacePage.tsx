import React, { useState, useEffect } from 'react';
import {
  FileCode2,
  FolderTree,
  Terminal,
  Play,
  CheckCircle2,
  AlertCircle,
  Clock,
  Shield,
  Layers,
  Search,
  Code2,
  ChevronDown,
  ChevronRight,
  Maximize2,
  Minimize2,
  RefreshCw,
  GitCommit,
  Sparkles,
  FileText,
  X
} from 'lucide-react';
import {
  Workspace,
  Task,
  FileTreeNode,
  FileContentResponse,
  PatchDiff,
  TaskUnderstandingResult
} from '../types';
import { api } from '../services/api';

interface EngineeringWorkspaceProps {
  activeWorkspace?: Workspace;
  activeTask?: Task;
  tasks: Task[];
  onRefresh: () => void;
  onNavigate: (tab: string) => void;
}

export const EngineeringWorkspacePage: React.FC<EngineeringWorkspaceProps> = ({
  activeWorkspace,
  activeTask,
  tasks,
  onRefresh,
  onNavigate,
}) => {
  // Navigation & Panel states
  const [fileTree, setFileTree] = useState<FileTreeNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [openTabs, setOpenTabs] = useState<{ path: string; name: string }[]>([]);
  const [activeTabPath, setActiveTabPath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContentResponse | null>(null);
  const [bottomPanelOpen, setBottomPanelOpen] = useState(true);
  const [bottomTab, setBottomTab] = useState<'tests' | 'logs' | 'diffs'>('tests');

  // Task generation state
  const [taskPrompt, setTaskPrompt] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<TaskUnderstandingResult | null>(null);
  const [diffs, setDiffs] = useState<PatchDiff[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (activeWorkspace) {
      loadFileTree();
    }
  }, [activeWorkspace]);

  useEffect(() => {
    if (activeTask) {
      loadDiffs();
    }
  }, [activeTask]);

  useEffect(() => {
    if (activeTabPath && activeWorkspace) {
      loadFileContent(activeTabPath);
    }
  }, [activeTabPath, activeWorkspace]);

  const loadFileTree = async () => {
    if (!activeWorkspace) return;
    try {
      const tree = await api.getRepoTree(activeWorkspace.id, 5);
      setFileTree(tree);
      // Auto open first file if no tabs open
      if (tree.children && tree.children.length > 0 && openTabs.length === 0) {
        const firstFile = findFirstFile(tree);
        if (firstFile) {
          openFile(firstFile.path, firstFile.name);
        }
      }
    } catch (err: any) {
      console.warn('Could not load repo tree:', err);
    }
  };

  const findFirstFile = (node: FileTreeNode): { path: string; name: string } | null => {
    if (node.type === 'file') return { path: node.path, name: node.name };
    if (node.children) {
      for (const child of node.children) {
        const found = findFirstFile(child);
        if (found) return found;
      }
    }
    return null;
  };

  const loadFileContent = async (path: string) => {
    if (!activeWorkspace) return;
    try {
      const res = await api.getRepoFile(activeWorkspace.id, path);
      setFileContent(res);
    } catch (err: any) {
      console.warn('Could not load file:', err);
    }
  };

  const loadDiffs = async () => {
    if (!activeTask) return;
    try {
      const d = await api.getDiffs(activeTask.id);
      setDiffs(d);
    } catch (err) {
      // ignore
    }
  };

  const openFile = (path: string, name: string) => {
    if (!openTabs.some((t) => t.path === path)) {
      setOpenTabs([...openTabs, { path, name }]);
    }
    setActiveTabPath(path);
  };

  const closeTab = (e: React.MouseEvent, path: string) => {
    e.stopPropagation();
    const nextTabs = openTabs.filter((t) => t.path !== path);
    setOpenTabs(nextTabs);
    if (activeTabPath === path) {
      setActiveTabPath(nextTabs.length > 0 ? nextTabs[nextTabs.length - 1].path : null);
      if (nextTabs.length === 0) setFileContent(null);
    }
  };

  const handleAnalyzeRequirement = async () => {
    if (!taskPrompt.trim() || !activeWorkspace) return;
    setIsAnalyzing(true);
    setStatusMessage('Analyzing engineering requirement and repo context...');
    try {
      const res = await api.analyzeRequirement({
        title: taskPrompt.slice(0, 60),
        description: taskPrompt,
        workspace_id: activeWorkspace.id,
      });
      setAnalysisResult(res);
      setStatusMessage('Requirement analyzed. Ready to create engineering task.');
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCreateAndExecute = async () => {
    if (!taskPrompt.trim() || !activeWorkspace) return;
    setIsExecuting(true);
    setStatusMessage('Creating task and generating dynamic DAG plan...');
    try {
      const task = await api.createTask({
        workspace_id: activeWorkspace.id,
        title: taskPrompt.slice(0, 60),
        description: taskPrompt,
      });

      setStatusMessage('Generating plan...');
      await api.generatePlan(task.id);

      setStatusMessage('Approving plan for isolated execution...');
      await api.approvePlan(task.id, 'APPROVED');

      setStatusMessage('Executing autonomous coding in sandboxed clone...');
      await api.executeCoding(task.id);

      setStatusMessage('Running test verification runner...');
      await api.runVerification(task.id);

      setStatusMessage('Task execution complete. Review diffs and test results below.');
      onRefresh();
    } catch (err: any) {
      setStatusMessage(`Error during execution: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  // Render file tree recursively
  const renderTree = (node: FileTreeNode, depth = 0) => {
    const isFile = node.type === 'file';
    const matchesSearch = !searchQuery || node.name.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch && isFile) return null;

    return (
      <div key={node.path} style={{ paddingLeft: `${depth * 12}px` }}>
        {isFile ? (
          <div
            onClick={() => openFile(node.path, node.name)}
            className={`flex items-center space-x-1.5 py-1 px-2 rounded cursor-pointer text-xs transition ${
              activeTabPath === node.path
                ? 'bg-cyan-500/15 text-cyan-300 font-semibold border-l-2 border-cyan-400'
                : 'text-slate-300 hover:bg-navy-800/80 hover:text-slate-100'
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <span className="truncate">{node.name}</span>
          </div>
        ) : (
          <div className="py-1 px-2 text-xs text-slate-400 font-medium flex items-center space-x-1.5 select-none">
            <FolderTree className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span className="truncate">{node.name}</span>
          </div>
        )}
        {node.children && node.children.map((child) => renderTree(child, depth + 1))}
      </div>
    );
  };

  const latestExecution = activeTask?.executions?.[0];

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-navy-950 font-mono select-none overflow-hidden">
      {/* Top Workspace Toolbar */}
      <div className="h-10 bg-navy-900 border-b border-navy-800 px-4 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <Code2 className="w-4 h-4 text-cyan-400" />
            <span className="font-bold text-slate-100">AI ENGINEERING WORKSPACE</span>
          </div>
          <span className="text-slate-400">|</span>
          <span className="text-slate-400">Workspace:</span>
          <span className="text-cyan-300 font-semibold">{activeWorkspace?.name || 'None'}</span>
        </div>

        <div className="flex items-center space-x-2 text-[11px]">
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Shield className="w-3 h-3" />
            <span>Isolated Sandbox Active</span>
          </span>
          <span className="px-2 py-0.5 rounded bg-navy-800 text-slate-300">
            Mac M1 8GB
          </span>
        </div>
      </div>

      {/* Main 3-Column Working Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* PANEL 1: LEFT FILE & SYMBOL EXPLORER */}
        <div className="w-64 bg-navy-900/90 border-r border-navy-800 flex flex-col flex-shrink-0">
          <div className="p-2.5 border-b border-navy-800">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search files & symbols..."
                className="w-full bg-navy-950 border border-navy-800 rounded px-2.5 pl-8 py-1 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            <p className="text-[10px] uppercase font-bold text-slate-400 px-2 py-1 tracking-wider">
              Files ({activeWorkspace?.name})
            </p>
            {fileTree ? renderTree(fileTree) : (
              <p className="text-xs text-slate-400 p-3 italic">Loading repository tree...</p>
            )}
          </div>
        </div>

        {/* PANEL 2: CENTER CODE EDITOR & TABS */}
        <div className="flex-1 flex flex-col bg-navy-950 overflow-hidden">
          {/* Tab Bar */}
          <div className="h-9 bg-navy-900 border-b border-navy-800 flex items-center px-2 space-x-1 overflow-x-auto flex-shrink-0">
            {openTabs.map((tab) => (
              <div
                key={tab.path}
                onClick={() => setActiveTabPath(tab.path)}
                className={`group flex items-center space-x-2 px-3 py-1 rounded-t text-xs cursor-pointer border-t-2 transition ${
                  activeTabPath === tab.path
                    ? 'bg-navy-950 text-cyan-300 font-semibold border-cyan-400'
                    : 'bg-navy-900 text-slate-400 hover:text-slate-200 border-transparent hover:bg-navy-850'
                }`}
              >
                <FileCode2 className="w-3.5 h-3.5 text-cyan-400" />
                <span className="truncate max-w-[120px]">{tab.name}</span>
                <button
                  onClick={(e) => closeTab(e, tab.path)}
                  className="opacity-0 group-hover:opacity-100 hover:text-rose-400 text-slate-400 rounded p-0.5 transition"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>

          {/* Code Viewer / Editor Area */}
          <div className="flex-1 overflow-auto bg-navy-950 flex text-xs">
            {fileContent ? (
              <div className="w-full flex">
                {/* Line Numbers */}
                <div className="w-12 bg-navy-900/40 text-slate-400 text-right pr-3 pt-3 select-none flex-shrink-0 border-r border-navy-800/40">
                  {Array.from({ length: fileContent.line_count || 1 }).map((_, i) => (
                    <div key={i} className="leading-5 text-[11px] font-mono">{i + 1}</div>
                  ))}
                </div>

                {/* File Contents */}
                <pre className="flex-1 p-3 text-slate-200 overflow-x-auto font-mono text-xs leading-5 select-text">
                  <code>{fileContent.content}</code>
                </pre>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 space-y-2">
                <FileCode2 className="w-10 h-10 text-navy-700" />
                <p className="text-xs">Select a file from the repository tree to inspect or edit.</p>
              </div>
            )}
          </div>

          {/* Editor Status Bar */}
          <div className="h-6 bg-navy-900 border-t border-navy-800 px-4 flex items-center justify-between text-[11px] text-slate-400">
            <div className="flex items-center space-x-3">
              <span>{fileContent?.language || 'Plain Text'}</span>
              <span>{fileContent?.line_count || 0} lines</span>
              <span>{fileContent?.size_bytes || 0} bytes</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>UTF-8</span>
            </div>
          </div>
        </div>

        {/* PANEL 3: RIGHT AI CONVERSATION & TASK ORCHESTRATION */}
        <div className="w-96 bg-navy-900/90 border-l border-navy-800 flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-navy-800 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-100 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>AI Task Orchestrator</span>
            </span>
            <button
              onClick={onRefresh}
              className="p-1 hover:bg-navy-800 rounded text-slate-400 hover:text-slate-200 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Prompt Input Box */}
          <div className="p-3 border-b border-navy-800 space-y-2 bg-navy-950/40">
            <label className="text-[11px] text-slate-400 uppercase font-bold tracking-wider">
              Engineering Requirement
            </label>
            <textarea
              value={taskPrompt}
              onChange={(e) => setTaskPrompt(e.target.value)}
              placeholder="e.g. Find and fix the token expiry bug in auth.py, generate regression tests, and verify..."
              className="w-full h-20 bg-navy-950 border border-navy-700 rounded-lg p-2 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 font-mono resize-none"
            />

            <div className="flex items-center space-x-2">
              <button
                onClick={handleAnalyzeRequirement}
                disabled={isAnalyzing || !taskPrompt.trim()}
                className="flex-1 py-1.5 bg-navy-800 hover:bg-navy-700 disabled:opacity-50 text-slate-200 rounded text-xs font-semibold flex items-center justify-center space-x-1 transition"
              >
                {isAnalyzing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                <span>Analyze (AI)</span>
              </button>

              <button
                onClick={handleCreateAndExecute}
                disabled={isExecuting || !taskPrompt.trim()}
                className="flex-1 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center justify-center space-x-1 shadow-sm transition"
              >
                {isExecuting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                <span>Auto Execute</span>
              </button>
            </div>

            {statusMessage && (
              <p className="text-[10px] text-cyan-400 italic bg-cyan-500/10 p-1.5 rounded border border-cyan-500/20">
                {statusMessage}
              </p>
            )}
          </div>

          {/* AI Understanding Summary */}
          {analysisResult && (
            <div className="p-3 border-b border-navy-800 bg-navy-950/60 text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Intent:</span>
                <span className="font-semibold text-cyan-300">{analysisResult.intent}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Risk Assessment:</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  analysisResult.risk_level === 'LOW'
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : 'bg-amber-500/10 text-amber-400'
                }`}>
                  {analysisResult.risk_level}
                </span>
              </div>
            </div>
          )}

          {/* Active Task Progress / Plan Steps */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              Active Task State {activeTask ? `(${activeTask.id.slice(0, 8)})` : ''}
            </p>

            {activeTask ? (
              <div className="space-y-2 text-xs">
                <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200 truncate">{activeTask.title}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-bold">
                      {activeTask.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">Phase: {activeTask.current_phase}</p>
                </div>

                {activeTask.plan_steps && activeTask.plan_steps.length > 0 && (
                  <div className="space-y-1 pt-1">
                    <p className="text-[10px] uppercase font-bold text-slate-400">Plan Steps (Topological DAG)</p>
                    {activeTask.plan_steps.map((s, idx) => (
                      <div
                        key={s.id || idx}
                        className="p-2 rounded bg-navy-950/80 border border-navy-800/80 text-[11px] flex items-center justify-between"
                      >
                        <span className="text-slate-300 truncate">{s.step_order || idx + 1}. {s.title}</span>
                        <span className="text-[10px] text-emerald-400 font-semibold">{s.status}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-400 text-xs italic">
                No active engineering task. Enter a requirement above to begin.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* PANEL 4: BOTTOM COLLAPSIBLE TEST & EXECUTION DRAWER */}
      <div className={`bg-navy-900 border-t border-navy-800 transition-all ${
        bottomPanelOpen ? 'h-52' : 'h-8'
      } flex flex-col flex-shrink-0`}>
        {/* Bottom Drawer Header */}
        <div className="h-8 bg-navy-950 px-4 flex items-center justify-between border-b border-navy-800 text-xs">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setBottomTab('tests')}
              className={`py-1 font-semibold transition ${
                bottomTab === 'tests' ? 'text-cyan-400 border-b border-cyan-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Test Verification
            </button>
            <button
              onClick={() => setBottomTab('diffs')}
              className={`py-1 font-semibold transition ${
                bottomTab === 'diffs' ? 'text-cyan-400 border-b border-cyan-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Generated Patches ({diffs.length})
            </button>
            <button
              onClick={() => setBottomTab('logs')}
              className={`py-1 font-semibold transition ${
                bottomTab === 'logs' ? 'text-cyan-400 border-b border-cyan-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Runner Logs
            </button>
          </div>

          <button
            onClick={() => setBottomPanelOpen(!bottomPanelOpen)}
            className="text-slate-400 hover:text-slate-200 transition"
          >
            {bottomPanelOpen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Bottom Drawer Content */}
        {bottomPanelOpen && (
          <div className="flex-1 overflow-auto p-3 text-xs bg-navy-950/90 text-slate-300 font-mono">
            {bottomTab === 'tests' && (
              <div>
                {latestExecution ? (
                  <div className="space-y-1.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-200">Command:</span>
                      <code className="text-cyan-300">{latestExecution.command}</code>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        latestExecution.exit_code === 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        Exit Code: {latestExecution.exit_code}
                      </span>
                      <span className="text-slate-400 text-[11px]">({latestExecution.duration_ms}ms)</span>
                    </div>
                    <pre className="p-2.5 rounded bg-navy-900 border border-navy-800 text-[11px] overflow-x-auto text-slate-300">
                      {latestExecution.stdout || latestExecution.stderr || 'No output recorded.'}
                    </pre>
                  </div>
                ) : (
                  <p className="text-slate-400 italic">No verification runs executed yet for active task.</p>
                )}
              </div>
            )}

            {bottomTab === 'diffs' && (
              <div className="space-y-2">
                {diffs.length > 0 ? (
                  diffs.map((d, i) => (
                    <div key={i} className="p-2 rounded bg-navy-900 border border-navy-800 space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-cyan-300">{d.file_path}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-navy-800 text-slate-300">{d.status}</span>
                      </div>
                      <pre className="text-[11px] text-slate-300 overflow-x-auto">
                        {d.diff_text}
                      </pre>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400 italic">No patches generated yet.</p>
                )}
              </div>
            )}

            {bottomTab === 'logs' && (
              <div className="text-slate-400 text-[11px] space-y-1">
                <p>[SYSTEM] Sandbox environment initialized: isolated/task_workspace</p>
                <p>[SECURITY] Path containment enforced: ALLOWED_REPO_ROOTS</p>
                <p>[RUNNER] Allowlisted test executables: pytest, vitest, npm test</p>
                <p>[STATE] Task status: {activeTask?.status || 'IDLE'}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
