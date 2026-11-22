import React, { useState } from 'react';
import { Terminal, Send, XCircle, AlertCircle, PlayCircle, ShieldCheck, Sparkles, HelpCircle, CheckSquare, AlertTriangle } from 'lucide-react';
import { Workspace, Task, TaskUnderstandingResult } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';

interface TaskConsolePageProps {
  tasks: Task[];
  activeWorkspace?: Workspace;
  onRefresh: () => void;
  onNavigate: (tab: string) => void;
}

export const TaskConsolePage: React.FC<TaskConsolePageProps> = ({
  tasks,
  activeWorkspace,
  onRefresh,
  onNavigate,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(tasks[0] || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [understanding, setUnderstanding] = useState<TaskUnderstandingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!title.trim() && !description.trim()) {
      setError('Enter a title or description to analyze.');
      return;
    }
    setIsAnalyzing(true);
    setError(null);
    try {
      const res = await api.analyzeRequirement({
        title: title.trim(),
        description: description.trim(),
        workspace_id: activeWorkspace?.id,
      });
      setUnderstanding(res);
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace) {
      setError('Please select or create an active workspace first.');
      return;
    }
    if (!title.trim() || !description.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const newTask = await api.createTask({
        workspace_id: activeWorkspace.id,
        title: title.trim(),
        description: description.trim(),
      });
      setTitle('');
      setDescription('');
      setUnderstanding(null);
      onRefresh();
      setSelectedTask(newTask);
    } catch (err: any) {
      setError(err.message || 'Failed to create task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await api.cancelTask(taskId);
      onRefresh();
    } catch (err: any) {
      alert(`Error cancelling task: ${err.message}`);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <Terminal className="w-5 h-5 text-cyan-400" />
            <span>AI Task Console</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Dispatch engineering requirements to the autonomous orchestrator.
          </p>
        </div>

        {activeWorkspace && (
          <div className="text-xs px-3 py-1.5 rounded bg-navy-900 border border-navy-800 text-slate-300">
            Target: <span className="text-cyan-400 font-semibold">{activeWorkspace.name}</span>
          </div>
        )}
      </div>

      {/* Grid: Task Form & Active Task Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Requirement Dispatcher */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 space-y-4">
            <h3 className="text-xs uppercase font-semibold text-slate-300 tracking-wider">
              Dispatch Requirement
            </h3>

            {error && (
              <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-400 flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreateTask} className="space-y-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Task Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Fix authentication JWT expiry bug"
                  required
                  className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Requirement & Instructions</label>
                <textarea
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe bug symptoms, required changes, test requirements, or performance criteria..."
                  required
                  className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 resize-none"
                />
              </div>

              {understanding && (
                <div className="p-3 bg-navy-950 rounded-lg border border-navy-700 space-y-2 text-[11px]">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-cyan-400 flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{understanding.intent} ({understanding.category})</span>
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      understanding.risk_level === 'CRITICAL' || understanding.risk_level === 'HIGH'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      RISK: {understanding.risk_level}
                    </span>
                  </div>

                  {understanding.ambiguity.is_ambiguous && (
                    <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded text-amber-300 text-[10px] space-y-1">
                      <div className="font-semibold flex items-center space-x-1">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Ambiguity Detected (Score: {understanding.ambiguity.ambiguity_score})</span>
                      </div>
                      {understanding.ambiguity.clarification_questions.map((q, i) => (
                        <p key={i}>• {q}</p>
                      ))}
                    </div>
                  )}

                  {understanding.acceptance_criteria.length > 0 && (
                    <div className="space-y-1 pt-1 border-t border-navy-800">
                      <span className="text-[10px] uppercase text-slate-400 font-bold block">Acceptance Criteria</span>
                      {understanding.acceptance_criteria.map((c) => (
                        <div key={c.id} className="flex items-start space-x-1.5 text-slate-300 text-[10px]">
                          <CheckSquare className="w-3 h-3 text-cyan-400 flex-shrink-0 mt-0.5" />
                          <span>{c.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || (!title.trim() && !description.trim())}
                  className="px-3 py-2 bg-navy-800 hover:bg-navy-700 disabled:opacity-50 text-cyan-400 border border-navy-700 rounded text-xs font-semibold flex items-center space-x-1.5 transition"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{isAnalyzing ? 'Analyzing...' : 'Analyze Requirement (AI)'}</span>
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !activeWorkspace}
                  className="flex-1 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center justify-center space-x-2 transition"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{isSubmitting ? 'Starting Plan...' : 'Dispatch Task'}</span>
                </button>
              </div>
            </form>

            <div className="text-[10px] text-slate-400 flex items-center space-x-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              <span>Generates structured plan before any file modifications.</span>
            </div>
          </div>

          {/* Task History list */}
          <div className="bg-navy-900 border border-navy-800 rounded-xl p-4 space-y-3">
            <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
              Task History ({tasks.length})
            </h4>
            <div className="max-h-80 overflow-y-auto space-y-2">
              {tasks.map((t) => {
                const isSelected = selectedTask?.id === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setSelectedTask(t)}
                    className={`p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                      isSelected
                        ? 'border-cyan-500 bg-navy-850'
                        : 'border-navy-800 hover:border-navy-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-200 truncate">{t.title}</span>
                      <StatusBadge status={t.status} size="sm" />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1 truncate">{t.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Col: Active Task Inspector */}
        <div className="lg:col-span-2 space-y-6">
          {selectedTask ? (
            <div className="bg-navy-900 border border-navy-800 rounded-xl p-6 space-y-6">
              <div className="flex items-start justify-between border-b border-navy-800 pb-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-base font-bold text-slate-100">{selectedTask.title}</h3>
                    <StatusBadge status={selectedTask.status} />
                  </div>
                  <p className="text-xs text-slate-400">Task ID: {selectedTask.id}</p>
                </div>

                {['PENDING', 'PLANNING', 'CODING', 'VERIFYING', 'DEBUGGING'].includes(selectedTask.status) && (
                  <button
                    onClick={() => handleCancelTask(selectedTask.id)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-xs transition"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Cancel Task</span>
                  </button>
                )}
              </div>

              {/* Requirement Text */}
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Requirement</span>
                <p className="text-xs text-slate-300 bg-navy-950 p-3 rounded border border-navy-800 whitespace-pre-wrap">
                  {selectedTask.description}
                </p>
              </div>

              {/* Phase progress track */}
              <div className="space-y-2">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Current Phase</span>
                <div className="p-3 bg-navy-950 rounded border border-navy-800 flex items-center justify-between text-xs">
                  <span className="text-cyan-400 font-bold">{selectedTask.current_phase}</span>
                  <span className="text-slate-400">Repairs: {selectedTask.repair_attempts} / 3</span>
                </div>
              </div>

              {/* Next Steps Buttons */}
              <div className="pt-4 border-t border-navy-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">Created: {new Date(selectedTask.created_at).toLocaleString()}</span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => onNavigate('planning')}
                    className="px-3 py-1.5 rounded bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700"
                  >
                    View Plan Steps
                  </button>
                  <button
                    onClick={() => onNavigate('diff-review')}
                    className="px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
                  >
                    Inspect Code Diffs
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center text-xs text-slate-400">
              Select a task from the history or dispatch a new requirement above.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

