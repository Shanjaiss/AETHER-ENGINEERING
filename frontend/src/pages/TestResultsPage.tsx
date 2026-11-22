import React, { useState } from 'react';
import { FlaskConical, CheckCircle2, XCircle, Clock, Terminal } from 'lucide-react';
import { Task } from '../types';

interface TestResultsPageProps {
  activeTask?: Task;
}

export const TestResultsPage: React.FC<TestResultsPageProps> = ({ activeTask }) => {
  const executions = activeTask?.executions || [];
  const [selectedRunId, setSelectedRunId] = useState<string | null>(executions[0]?.id || null);

  const selectedRun = executions.find((r) => r.id === selectedRunId) || executions[0];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 font-mono">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <FlaskConical className="w-5 h-5 text-cyan-400" />
          <span>Verification & Self-Debugging Console</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Inspect sandboxed test discoveries, execution logs, failure diagnosis, and bounded repair iterations.
        </p>
      </div>

      {executions.length === 0 ? (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center text-xs text-slate-400">
          No test executions recorded for this task yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Execution list */}
          <div className="lg:col-span-1 space-y-2">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Execution Runs ({executions.length})
            </h3>
            {executions.map((run) => {
              const isSelected = selectedRun?.id === run.id;
              const isSuccess = run.status === 'SUCCESS';
              return (
                <button
                  key={run.id}
                  onClick={() => setSelectedRunId(run.id)}
                  className={`w-full text-left p-3 rounded-lg border text-xs transition ${
                    isSelected
                      ? 'bg-navy-850 border-cyan-500'
                      : 'bg-navy-900 border-navy-800 hover:border-navy-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{run.phase}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      isSuccess
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}>
                      {run.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate mt-1">{run.command}</p>
                  <div className="flex items-center space-x-3 text-[10px] text-slate-400 mt-2">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{run.duration_ms}ms</span>
                    </span>
                    <span>Exit: {run.exit_code}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Terminal log output */}
          <div className="lg:col-span-2 bg-navy-900 border border-navy-800 rounded-xl overflow-hidden flex flex-col h-[600px]">
            <div className="p-3 bg-navy-950 border-b border-navy-800 flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200 flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>Command: {selectedRun?.command}</span>
              </span>
              <span className="text-[11px] text-slate-400">Exit Code: {selectedRun?.exit_code}</span>
            </div>

            <div className="p-4 bg-navy-950/70 font-mono text-xs flex-1 overflow-y-auto space-y-4">
              {selectedRun?.stdout && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Standard Output</span>
                  <pre className="text-slate-300 whitespace-pre-wrap">{selectedRun.stdout}</pre>
                </div>
              )}

              {selectedRun?.stderr && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-rose-400 block mb-1">Standard Error</span>
                  <pre className="text-rose-300 whitespace-pre-wrap">{selectedRun.stderr}</pre>
                </div>
              )}

              {!selectedRun?.stdout && !selectedRun?.stderr && (
                <div className="text-slate-400 text-center py-12">No console output recorded.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

