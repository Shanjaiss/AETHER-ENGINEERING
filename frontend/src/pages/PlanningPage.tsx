import React, { useState } from 'react';
import { ListTree, CheckCircle, XCircle, AlertTriangle, Play, Sparkles, RefreshCw } from 'lucide-react';
import { Task } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';

interface PlanningPageProps {
  activeTask?: Task;
  onRefresh: () => void;
}

export const PlanningPage: React.FC<PlanningPageProps> = ({ activeTask, onRefresh }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleGeneratePlan = async () => {
    if (!activeTask) return;
    setIsProcessing(true);
    setActionError(null);
    try {
      await api.generatePlan(activeTask.id);
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Plan generation failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = async () => {
    if (!activeTask) return;
    setIsProcessing(true);
    setActionError(null);
    try {
      // 1. Approve plan
      await api.approvePlan(activeTask.id, 'APPROVED', 'Developer approved plan');
      // 2. Trigger isolated coding
      await api.executeCoding(activeTask.id);
      // 3. Trigger test verification & self-debugging
      await api.runVerification(activeTask.id);
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Execution error');
      onRefresh();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!activeTask) return;
    setIsProcessing(true);
    setActionError(null);
    try {
      await api.approvePlan(activeTask.id, 'REJECTED', 'Plan rejected by developer');
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Rejection error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6 font-mono">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <ListTree className="w-5 h-5 text-cyan-400" />
            <span>AI Planning Workspace</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Structured step-by-step engineering plan with file predictions and human approval gate.
          </p>
        </div>

        {activeTask && (
          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-400">Task: {activeTask.title}</span>
            <StatusBadge status={activeTask.status} size="sm" />
          </div>
        )}
      </div>

      {actionError && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-400 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {!activeTask ? (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center text-xs text-slate-400">
          No task selected. Select or launch a task in the AI Task Console first.
        </div>
      ) : activeTask.plan_steps.length === 0 ? (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center space-y-4">
          <ListTree className="w-10 h-10 text-cyan-400 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-slate-200">No Plan Generated Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Analyze the repository files and requirement specifications to produce an actionable plan.
            </p>
          </div>
          <button
            onClick={handleGeneratePlan}
            disabled={isProcessing}
            className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-semibold inline-flex items-center space-x-2 shadow-sm transition"
          >
            {isProcessing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>{isProcessing ? 'Generating Structured Plan...' : 'Generate AI Implementation Plan'}</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {activeTask.plan_steps.map((step) => (
            <div key={step.id} className="bg-navy-900 border border-navy-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="w-6 h-6 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 flex items-center justify-center text-xs font-bold">
                    {step.step_order}
                  </span>
                  <h4 className="text-sm font-semibold text-slate-100">{step.title}</h4>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded border ${
                    step.risk_level === 'HIGH'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      : step.risk_level === 'MEDIUM'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  }`}>
                    RISK: {step.risk_level}
                  </span>
                  <StatusBadge status={step.status} size="sm" />
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{step.description}</p>

              {step.target_files && step.target_files.length > 0 && (
                <div className="pt-2 border-t border-navy-800/60 flex items-center space-x-2">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Target Files:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {step.target_files.map((file, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-navy-950 text-cyan-300 rounded text-[11px] border border-navy-700">
                        {file}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Approval Gate Banner */}
          {activeTask.status === 'AWAITING_PLAN_APPROVAL' && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-amber-300">Human Approval Required</h4>
                  <p className="text-xs text-amber-200/80">
                    Review the plan steps above. Approving will create an isolated workspace copy and execute patches.
                  </p>
                </div>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={handleReject}
                  disabled={isProcessing}
                  className="px-4 py-2 bg-navy-800 hover:bg-navy-700 disabled:opacity-50 text-rose-400 border border-rose-500/30 rounded text-xs font-semibold flex items-center space-x-1.5 transition"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  <span>Reject Plan</span>
                </button>
                <button
                  onClick={handleApprove}
                  disabled={isProcessing}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition"
                >
                  {isProcessing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                  <span>{isProcessing ? 'Executing...' : 'Approve & Execute'}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
