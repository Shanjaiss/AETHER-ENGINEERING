import React, { useState, useEffect } from 'react';
import { Settings, ShieldCheck, Sparkles, Key, HardDrive, RefreshCw, Check, AlertCircle } from 'lucide-react';
import { HealthResponse, SettingsResponse } from '../types';
import { api } from '../services/api';

interface SettingsPageProps {
  health?: HealthResponse;
  onRefresh: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ health, onRefresh }) => {
  const [provider, setProvider] = useState('unconfigured');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [ollamaUrl, setOllamaUrl] = useState('http://127.0.0.1:11434');
  const [currentSettings, setCurrentSettings] = useState<SettingsResponse | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const s = await api.getSettings();
      setCurrentSettings(s);
      setProvider(s.llm_provider || 'unconfigured');
      setModel(s.llm_model || '');
      setOllamaUrl(s.ollama_base_url || 'http://127.0.0.1:11434');
    } catch (err: any) {
      setError(err.message || 'Failed to load settings');
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);
    try {
      const payload: any = {
        llm_provider: provider,
        llm_model: model,
        ollama_base_url: ollamaUrl,
      };
      if (apiKey) {
        if (provider === 'openai') payload.openai_api_key = apiKey;
        else if (provider === 'gemini') payload.gemini_api_key = apiKey;
        else if (provider === 'anthropic') payload.anthropic_api_key = apiKey;
      }
      const updated = await api.updateSettings(payload);
      setCurrentSettings(updated);
      setSaveSuccess(true);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to update settings');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6 font-mono">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <Settings className="w-5 h-5 text-cyan-400" />
          <span>System Settings & LLM Gateway</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Configure AI provider adapters, allowed workspace boundaries, and execution sandbox policies.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-xs text-emerald-400 flex items-center space-x-2">
          <Check className="w-4 h-4 flex-shrink-0" />
          <span>System settings updated successfully.</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-400 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* AI Provider Config Form */}
      <form onSubmit={handleSave} className="bg-navy-900 border border-navy-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-navy-800 pb-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>LLM Provider Configuration</span>
          </h3>
          <span className="text-[11px] text-slate-400">
            Active: <span className="text-cyan-400 font-bold">{currentSettings?.llm_provider || 'unconfigured'}</span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Provider Adapter</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="unconfigured">Unconfigured (Safe mode / Rule 15)</option>
              <option value="gemini">Google Gemini (Gemini 2.5 Flash / Pro)</option>
              <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
              <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              <option value="ollama">Local Ollama (DeepSeek-Coder, Llama 3)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">Model Name / Identifier</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. gemini-2.5-flash or gpt-4o-mini"
              className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {provider === 'ollama' ? (
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Ollama Base URL</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                placeholder="http://127.0.0.1:11434"
                className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>
          ) : provider !== 'unconfigured' ? (
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">API Key / Token</label>
              <div className="relative">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter API key (stored in memory, never logged)..."
                  className="w-full bg-navy-950 border border-navy-700 rounded pl-9 pr-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
                <Key className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>
          ) : null}
        </div>

        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition"
          >
            {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            <span>{isSaving ? 'Updating...' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>

      {/* Security Policies */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>Security & Execution Boundaries</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-navy-950 rounded border border-navy-800 space-y-1">
            <span className="font-semibold text-slate-300">Allowed Repository Roots</span>
            <p className="text-[11px] text-slate-400 truncate">
              {currentSettings?.allowed_repo_roots.join(', ') || '/Users/shanjaisenthil/Documents'}
            </p>
          </div>
          <div className="p-3 bg-navy-950 rounded border border-navy-800 space-y-1">
            <span className="font-semibold text-slate-300">Sandbox Process Timeout</span>
            <p className="text-[11px] text-slate-400">{currentSettings?.isolated_sandbox_timeout_seconds || 60} seconds</p>
          </div>
          <div className="p-3 bg-navy-950 rounded border border-navy-800 space-y-1">
            <span className="font-semibold text-slate-300">Maximum Repair Attempts</span>
            <p className="text-[11px] text-slate-400">{currentSettings?.max_repair_attempts || 3} attempts per failure</p>
          </div>
          <div className="p-3 bg-navy-950 rounded border border-navy-800 space-y-1">
            <span className="font-semibold text-slate-300">Target Hardware</span>
            <p className="text-[11px] text-emerald-400 font-semibold">Apple Silicon Mac M1 (8 GB Unified)</p>
          </div>
        </div>
      </div>
    </div>
  );
};
