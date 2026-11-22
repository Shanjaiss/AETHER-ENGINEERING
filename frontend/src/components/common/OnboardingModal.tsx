import React from 'react';
import {
  Sparkles,
  CheckCircle2,
  Shield,
  Layers,
  FileCode2,
  Terminal,
  Play,
  ArrowRight,
  Cpu,
  BarChart3,
  X
} from 'lucide-react';

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartDemo?: () => void;
  onNavigate?: (tab: string) => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onClose,
  onStartDemo,
  onNavigate,
}) => {
  if (!isOpen) return null;

  const steps = [
    {
      num: 1,
      title: 'Import Repository Safely',
      desc: 'Connect any local repository. Path containment ensures no files outside allowed workspace roots are ever accessed.',
      icon: FileCode2,
    },
    {
      num: 2,
      title: 'Natural-Language Task Understanding',
      desc: 'Input bugs or feature requirements. The AI classifies intent, ambiguity, and risk level with zero prompt injection escape.',
      icon: Terminal,
    },
    {
      num: 3,
      title: 'Dynamic Topological Planning',
      desc: 'Generates structured implementation plans ordered via Kahn DAG topological sorting with cycle detection and scope creep containment.',
      icon: Layers,
    },
    {
      num: 4,
      title: 'Human-in-the-Loop Plan Approval',
      desc: 'Developers retain full sovereignty. The agent is privilege-gated and cannot modify any code without explicit human approval.',
      icon: Shield,
    },
    {
      num: 5,
      title: 'Isolated Workspace Execution',
      desc: 'Code modifications execute exclusively in a sandboxed cloned directory; your original repository remains bit-for-bit identical.',
      icon: Cpu,
    },
    {
      num: 6,
      title: 'Independent Empirical Verification',
      desc: 'Allowlisted test runners execute real test suites. Success requires actual zero exit codes (exit_code == 0) — no faked test passes.',
      icon: CheckCircle2,
    },
    {
      num: 7,
      title: 'Code Review & Atomic Merge',
      desc: 'Review unified diffs with syntax coloration, inspect security blast radius, and approve or rollback changes with a single click.',
      icon: Play,
    },
    {
      num: 8,
      title: 'Evaluation Lab Benchmarking',
      desc: 'Scientific evaluation across 50 controlled engineering benchmarks, SWE-bench Lite adapter, and 12-vector adversarial security.',
      icon: BarChart3,
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-navy-900 border border-navy-700 w-full max-w-3xl rounded-2xl p-6 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto font-mono">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-navy-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Welcome to AETHER ENGINEER</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  v1.2.0
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                From Requirement to Verified Code — Autonomous AI Software Engineering Platform
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-navy-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {steps.map((s) => {
            const Icon = s.icon;
            return (
              <div
                key={s.num}
                className="bg-navy-950/70 border border-navy-800/80 p-3.5 rounded-xl space-y-1.5 hover:border-navy-700 transition"
              >
                <div className="flex items-center space-x-2.5">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/10 text-cyan-400 text-[10px] font-bold flex items-center justify-center border border-cyan-500/20">
                    {s.num}
                  </span>
                  <Icon className="w-4 h-4 text-cyan-400" />
                  <h4 className="text-xs font-semibold text-slate-200">{s.title}</h4>
                </div>
                <p className="text-[11px] text-slate-400 pl-7 leading-relaxed">{s.desc}</p>
              </div>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="pt-4 border-t border-navy-800 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2 text-[11px] text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Verified for Apple Silicon Mac M1 (8 GB RAM)</span>
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-navy-800 hover:bg-navy-700 text-slate-300 rounded-lg text-xs font-semibold flex-1 sm:flex-none transition"
            >
              Explore Workspace
            </button>
            <button
              onClick={() => {
                onClose();
                if (onNavigate) {
                  onNavigate('workspace-ide');
                } else if (onStartDemo) {
                  onStartDemo();
                }
              }}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 flex-1 sm:flex-none shadow-sm transition"
            >
              <span>Launch Recruiter Demo</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
