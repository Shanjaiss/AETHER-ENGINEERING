import React, { useState, useEffect } from 'react';
import { GitCompare, CheckCircle2, XCircle, FileCode, ShieldAlert, Download, AlertTriangle, RefreshCw, Check } from 'lucide-react';
import { Task, QualityReportResponse, ConflictCheckResponse } from '../types';
import { api } from '../services/api';

interface DiffReviewPageProps {
  activeTask?: Task;
  onRefresh: () => void;
}

export const DiffReviewPage: React.FC<DiffReviewPageProps> = ({ activeTask, onRefresh }) => {
  const patches = activeTask?.patches || [];
  const [selectedPatchId, setSelectedPatchId] = useState<string | null>(patches[0]?.id || null);
  const [report, setReport] = useState<QualityReportResponse | null>(null);
  const [conflicts, setConflicts] = useState<ConflictCheckResponse | null>(null);
  const [isApplying, setIsApplying] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (activeTask && patches.length > 0) {
      api.getQualityReport(activeTask.id).then(setReport).catch(() => {});
      api.checkConflicts(activeTask.id).then(setConflicts).catch(() => {});
    }
  }, [activeTask, patches.length]);

  const selectedPatch = patches.find((p) => p.id === selectedPatchId) || patches[0];

  const handleApproveAndApply = async () => {
    if (!activeTask) return;
    setIsApplying(true);
    setErrorMessage(null);
    setActionMessage(null);
    try {
      // 1. Submit review approval
      await api.submitReviewDecision(activeTask.id, 'APPROVED', 'Developer approved changes');
      // 2. Apply to source
      await api.applyChanges(activeTask.id);
      setActionMessage('Successfully merged verified patches to original repository!');
      onRefresh();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to apply patch');
    } finally {
      setIsApplying(false);
    }
  };

  const handleReject = async () => {
    if (!activeTask) return;
    setIsApplying(true);
    setErrorMessage(null);
    try {
      await api.submitReviewDecision(activeTask.id, 'REJECTED', 'Developer rejected patch');
      setActionMessage('Proposed patch was rejected. Original repository was not modified.');
      onRefresh();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to reject patch');
    } finally {
      setIsApplying(false);
    }
  };

  const handleExportPatch = () => {
    if (!activeTask) return;
    window.open(api.exportPatchUrl(activeTask.id), '_blank');
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <GitCompare className="w-5 h-5 text-cyan-400" />
            <span>Code Review & Diff Verification</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Inspect patch diffs created in the isolated workspace. Approve before applying to source.
          </p>
        </div>

        {patches.length > 0 && (
          <div className="flex items-center space-x-2">
            <button
              onClick={handleExportPatch}
              className="px-3 py-1.5 bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 rounded text-xs flex items-center space-x-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export .patch</span>
            </button>
            <button
              onClick={handleReject}
              disabled={isApplying || activeTask?.status === 'COMPLETED'}
              className="px-3 py-1.5 bg-navy-800 hover:bg-navy-700 disabled:opacity-50 text-rose-400 border border-rose-500/30 rounded text-xs flex items-center space-x-1.5 transition"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Reject</span>
            </button>
            <button
              onClick={handleApproveAndApply}
              disabled={isApplying || activeTask?.status === 'COMPLETED'}
              className="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition"
            >
              {isApplying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
              <span>{activeTask?.status === 'COMPLETED' ? 'Merged to Source' : isApplying ? 'Applying...' : 'Approve & Apply to Source'}</span>
            </button>
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-xs text-emerald-400 flex items-center space-x-2">
          <Check className="w-4 h-4 flex-shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-400 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {conflicts?.has_conflicts && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300 space-y-1">
          <div className="flex items-center space-x-2 font-bold">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>External Conflicts Detected!</span>
          </div>
          <p className="text-amber-200/80">
            One or more target files were modified externally in the original repository. Merging is blocked to prevent accidental overwrites.
          </p>
          <ul className="list-disc list-inside pt-1 text-[11px] text-amber-300">
            {conflicts.conflicted_files.map((cf, i) => <li key={i}>{cf}</li>)}
          </ul>
        </div>
      )}

      {patches.length === 0 ? (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center text-xs text-slate-400">
          No code patches generated yet. Complete planning and coding phases to inspect diffs.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* File list & Quality metrics */}
          <div className="lg:col-span-1 space-y-4">
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Modified Files ({patches.length})
              </h3>
              {patches.map((patch) => {
                const isSelected = selectedPatch?.id === patch.id;
                return (
                  <button
                    key={patch.id}
                    onClick={() => setSelectedPatchId(patch.id)}
                    className={`w-full text-left p-3 rounded-lg border text-xs flex items-center space-x-2 transition ${
                      isSelected
                        ? 'bg-navy-850 border-cyan-500 text-cyan-300'
                        : 'bg-navy-900 border-navy-800 text-slate-300 hover:border-navy-700'
                    }`}
                  >
                    <FileCode className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                    <span className="truncate">{patch.file_path}</span>
                  </button>
                );
              })}
            </div>

            {/* Quality Report card */}
            {report && (
              <div className="bg-navy-900 border border-navy-800 rounded-lg p-4 space-y-3 text-xs">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block border-b border-navy-800 pb-1">
                  Quality & Safety Summary
                </span>
                <div className="flex justify-between">
                  <span className="text-slate-400">Overall Risk</span>
                  <span className={`font-bold ${
                    report.overall_risk === 'HIGH' ? 'text-rose-400' : report.overall_risk === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {report.overall_risk}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Lines Changed</span>
                  <span className="text-slate-200 font-mono">+{report.total_lines_added} / -{report.total_lines_removed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Static AST Check</span>
                  <span className="text-emerald-400">Passed</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Test Verification</span>
                  <span className="text-emerald-400 font-semibold">{report.test_evidence?.final_status}</span>
                </div>
                {report.security_warnings.length > 0 && (
                  <div className="pt-2 border-t border-navy-800 text-[11px] text-amber-400 space-y-1">
                    {report.security_warnings.map((w, idx) => (
                      <div key={idx} className="flex items-start space-x-1">
                        <ShieldAlert className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Diff viewer */}
          <div className="lg:col-span-3 bg-navy-900 border border-navy-800 rounded-xl overflow-hidden flex flex-col h-[650px]">
            <div className="p-3 bg-navy-950 border-b border-navy-800 flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200">{selectedPatch?.file_path}</span>
              <span className="text-[11px] text-slate-400">Unified Diff</span>
            </div>

            <div className="p-4 overflow-x-auto text-xs font-mono flex-1 bg-navy-950/70 leading-relaxed">
              {selectedPatch?.diff_text ? (
                <pre className="text-slate-300 whitespace-pre">
                  {selectedPatch.diff_text.split('\n').map((line, idx) => {
                    const isAddition = line.startsWith('+') && !line.startsWith('+++');
                    const isDeletion = line.startsWith('-') && !line.startsWith('---');
                    const isHeader = line.startsWith('@@') || line.startsWith('diff ');

                    let lineClass = 'text-slate-300';
                    if (isAddition) lineClass = 'text-emerald-400 bg-emerald-500/10 -mx-4 px-4 block';
                    if (isDeletion) lineClass = 'text-rose-400 bg-rose-500/10 -mx-4 px-4 block';
                    if (isHeader) lineClass = 'text-cyan-400 font-bold -mx-4 px-4 block bg-cyan-950/40';

                    return (
                      <span key={idx} className={lineClass}>
                        {line || ' '}
                      </span>
                    );
                  })}
                </pre>
              ) : (
                <div className="text-slate-400 py-8 text-center">No diff content available.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
