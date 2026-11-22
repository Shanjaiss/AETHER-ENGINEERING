import React, { useState, useEffect } from 'react';
import { FileCode2, Search, Folder, FolderOpen, File, Layers, Code, ShieldCheck, RefreshCw, AlertTriangle, GitFork, ArrowRight, Activity } from 'lucide-react';
import { Workspace, FileTreeNode, FileContentResponse, CodeSearchResponse, DependencyGraphResponse, ChangeImpactReport } from '../types';
import { api } from '../services/api';

interface RepoExplorerPageProps {
  activeWorkspace?: Workspace;
}

export const RepoExplorerPage: React.FC<RepoExplorerPageProps> = ({ activeWorkspace }) => {
  const [tree, setTree] = useState<FileTreeNode | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileContentResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<CodeSearchResponse | null>(null);
  const [depGraph, setDepGraph] = useState<DependencyGraphResponse | null>(null);
  const [impactReport, setImpactReport] = useState<ChangeImpactReport | null>(null);
  const [activeTab, setActiveTab] = useState<'code' | 'dependencies'>('code');
  const [isLoading, setIsLoading] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Record<string, boolean>>({ '.': true });
  const [error, setError] = useState<string | null>(null);

  const repo = activeWorkspace?.repositories?.[0];

  useEffect(() => {
    if (activeWorkspace) {
      loadRepository();
    }
  }, [activeWorkspace?.id]);

  const loadRepository = async () => {
    if (!activeWorkspace) return;
    setIsLoading(true);
    setError(null);
    try {
      // 1. Scan / get summary
      const scanRes = await api.scanRepository(activeWorkspace.id, activeWorkspace.path);
      // 2. Fetch tree
      const treeData = await api.getRepoTree(scanRes.id);
      setTree(treeData);
      // 3. Fetch dependencies
      const deps = await api.getDependencies(scanRes.id);
      setDepGraph(deps);
    } catch (err: any) {
      setError(err.message || 'Failed to scan repository');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFile = async (filePath: string) => {
    if (!repo && !tree) return;
    const repoId = repo?.id || activeWorkspace?.repositories?.[0]?.id;
    if (!repoId) return;

    setError(null);
    try {
      const fileData = await api.getRepoFile(repoId, filePath);
      setSelectedFile(fileData);
      // Also fetch impact report
      const impact = await api.getChangeImpact(repoId, filePath);
      setImpactReport(impact);
    } catch (err: any) {
      setError(err.message || 'Failed to read file');
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const repoId = repo?.id || activeWorkspace?.repositories?.[0]?.id;
    if (!repoId || !searchQuery.trim()) return;

    setError(null);
    try {
      const res = await api.searchRepo(repoId, searchQuery.trim());
      setSearchResults(res);
    } catch (err: any) {
      setError(err.message || 'Search failed');
    }
  };

  const toggleDir = (dirPath: string) => {
    setExpandedDirs((prev) => ({ ...prev, [dirPath]: !prev[dirPath] }));
  };

  const renderTreeNode = (node: FileTreeNode, depth: number = 0) => {
    if (node.type === 'directory') {
      const isExpanded = expandedDirs[node.path] ?? depth < 2;
      return (
        <div key={node.path} className="select-none">
          <div
            onClick={() => toggleDir(node.path)}
            className="flex items-center space-x-1.5 py-1 px-1.5 rounded hover:bg-navy-800/60 cursor-pointer text-slate-300 text-xs"
            style={{ paddingLeft: `${depth * 14 + 6}px` }}
          >
            {isExpanded ? (
              <FolderOpen className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            ) : (
              <Folder className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
            )}
            <span className="font-semibold">{node.name}</span>
          </div>
          {isExpanded && node.children && (
            <div>
              {node.children.map((child) => renderTreeNode(child, depth + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <div
        key={node.path}
        onClick={() => handleSelectFile(node.path)}
        className={`flex items-center space-x-1.5 py-1 px-1.5 rounded cursor-pointer text-xs transition ${
          selectedFile?.relative_path === node.path
            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-navy-800/40'
        }`}
        style={{ paddingLeft: `${depth * 14 + 6}px` }}
      >
        <File className="w-3 h-3 text-slate-400 flex-shrink-0" />
        <span className="truncate">{node.name}</span>
        {node.size_bytes > 0 && (
          <span className="text-[10px] text-slate-400 ml-auto pl-1">
            {node.size_bytes > 1024 ? `${Math.round(node.size_bytes / 1024)}KB` : `${node.size_bytes}B`}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <FileCode2 className="w-5 h-5 text-cyan-400" />
            <span>Repository Intelligence Explorer</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Safe AST and structural index of target repository. Filtered against secret patterns and .gitignore.
          </p>
        </div>

        {activeWorkspace && (
          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-300 bg-navy-900 border border-navy-800 px-3 py-1.5 rounded">
              {activeWorkspace.name} ({activeWorkspace.path})
            </span>
            <button
              onClick={loadRepository}
              disabled={isLoading}
              className="p-1.5 rounded bg-navy-800 hover:bg-navy-700 text-slate-300 border border-navy-700"
              title="Rescan repository"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-400 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!activeWorkspace ? (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center text-xs text-slate-400">
          No active workspace selected. Select or register a workspace first.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Tech Detection, Search, Tree */}
          <div className="lg:col-span-1 space-y-4">
            {/* Tech stack card */}
            <div className="bg-navy-900 border border-navy-800 rounded-xl p-4 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>Detected Technologies</span>
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Languages</span>
                  <span className="text-slate-200">
                    {repo && Object.keys(repo.languages || {}).length > 0
                      ? Object.keys(repo.languages).join(', ')
                      : 'Python, TypeScript'}
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Frameworks</span>
                  <span className="text-slate-200">
                    {repo && repo.frameworks && repo.frameworks.length > 0
                      ? repo.frameworks.join(', ')
                      : 'FastAPI, React'}
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Git Repository</span>
                  <span className="text-emerald-400 font-medium">
                    {repo?.is_git ? `Branch: ${repo.default_branch}` : 'Initialized'}
                  </span>
                </div>
              </div>
            </div>

            {/* Code Search */}
            <div className="bg-navy-900 border border-navy-800 rounded-xl p-4 space-y-3">
              <form onSubmit={handleSearch} className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search repository..."
                  className="w-full bg-navy-950 border border-navy-700 rounded pl-8 pr-12 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
                <button
                  type="submit"
                  className="absolute right-1.5 top-1 px-2 py-0.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[10px]"
                >
                  Find
                </button>
              </form>

              {/* Search results list */}
              {searchResults && (
                <div className="max-h-48 overflow-y-auto space-y-1 text-xs border-t border-navy-800 pt-2">
                  <div className="text-[10px] text-slate-400 justify-between flex">
                    <span>Matches: {searchResults.total_matches}</span>
                    <button onClick={() => setSearchResults(null)} className="text-cyan-400 hover:underline">Clear</button>
                  </div>
                  {searchResults.results.map((res) => (
                    <div
                      key={res.relative_path}
                      onClick={() => handleSelectFile(res.relative_path)}
                      className="p-1.5 rounded bg-navy-950 hover:bg-navy-850 cursor-pointer"
                    >
                      <p className="font-semibold text-cyan-300 text-[11px] truncate">{res.relative_path}</p>
                      <p className="text-[10px] text-slate-400 truncate">{res.matches[0]?.line_text}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Real File Tree */}
              <div className="border-t border-navy-800 pt-3">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-2">
                  Codebase File Tree
                </span>
                <div className="max-h-80 overflow-y-auto space-y-0.5">
                  {tree ? (
                    tree.children && tree.children.length > 0 ? (
                      tree.children.map((child) => renderTreeNode(child, 0))
                    ) : (
                      <div className="text-slate-400 text-xs py-2">No files in directory.</div>
                    )
                  ) : (
                    <div className="text-slate-400 text-xs py-4 text-center">Loading file tree...</div>
                  )}
                </div>
              </div>

              <div className="pt-2 text-[10px] text-slate-400 flex items-center space-x-1.5 border-t border-navy-800">
                <ShieldCheck className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>Protected against .env files and credential leaks.</span>
              </div>
            </div>
          </div>

          {/* Right Column: File Preview & Intelligence Console */}
          <div className="lg:col-span-2 bg-navy-900 border border-navy-800 rounded-xl overflow-hidden flex flex-col h-[650px]">
            <div className="p-2.5 bg-navy-950 border-b border-navy-800 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveTab('code')}
                  className={`px-3 py-1 rounded text-xs font-semibold flex items-center space-x-1.5 transition ${
                    activeTab === 'code' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Code className="w-3.5 h-3.5" />
                  <span>Code Inspection</span>
                </button>
                <button
                  onClick={() => setActiveTab('dependencies')}
                  className={`px-3 py-1 rounded text-xs font-semibold flex items-center space-x-1.5 transition ${
                    activeTab === 'dependencies' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <GitFork className="w-3.5 h-3.5" />
                  <span>Dependency Graph & Blast Radius</span>
                </button>
              </div>

              {selectedFile && activeTab === 'code' && (
                <span className="text-[11px] text-slate-400">
                  {selectedFile.language} • {selectedFile.line_count} lines • {selectedFile.size_bytes}B
                </span>
              )}
            </div>

            <div className="p-4 bg-navy-950/60 font-mono text-xs flex-1 overflow-y-auto text-slate-300 leading-relaxed">
              {activeTab === 'code' ? (
                selectedFile ? (
                  <pre className="text-slate-300 whitespace-pre">
                    {selectedFile.content}
                  </pre>
                ) : (
                  <div className="text-slate-400 py-24 text-center">
                    Select a file from the repository tree on the left to inspect its contents safely.
                  </div>
                )
              ) : (
                <div className="space-y-6">
                  {/* Change Impact Analysis */}
                  {impactReport ? (
                    <div className="p-4 bg-navy-900 rounded-xl border border-navy-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-cyan-400 flex items-center space-x-2">
                          <Activity className="w-4 h-4" />
                          <span>Change Blast Radius: {impactReport.target_file}</span>
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          impactReport.risk_level === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}>
                          RISK: {impactReport.risk_level}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300">{impactReport.summary}</p>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-[11px]">
                        <div className="p-2.5 bg-navy-950 rounded border border-navy-800">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Directly Impacted Files</span>
                          {impactReport.directly_impacted_files.length > 0 ? (
                            <ul className="list-disc list-inside space-y-0.5 text-cyan-300">
                              {impactReport.directly_impacted_files.map((f, i) => <li key={i}>{f}</li>)}
                            </ul>
                          ) : (
                            <span className="text-slate-500">None</span>
                          )}
                        </div>

                        <div className="p-2.5 bg-navy-950 rounded border border-navy-800">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Associated Test Files</span>
                          {impactReport.associated_test_files.length > 0 ? (
                            <ul className="list-disc list-inside space-y-0.5 text-emerald-300">
                              {impactReport.associated_test_files.map((f, i) => <li key={i}>{f}</li>)}
                            </ul>
                          ) : (
                            <span className="text-slate-500">None</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-slate-400 text-center py-4">Select a file on the left to inspect its change impact.</div>
                  )}

                  {/* Dependency Graph Summary */}
                  {depGraph && (
                    <div className="p-4 bg-navy-900 rounded-xl border border-navy-800 space-y-3">
                      <h4 className="font-semibold text-slate-200 flex items-center space-x-2">
                        <GitFork className="w-4 h-4 text-cyan-400" />
                        <span>Dependency Graph ({depGraph.edges.length} Edges across {depGraph.nodes.length} Nodes)</span>
                      </h4>
                      <div className="max-h-60 overflow-y-auto space-y-1.5">
                        {depGraph.edges.map((e, idx) => (
                          <div key={idx} className="flex items-center space-x-2 text-[11px] bg-navy-950 p-2 rounded border border-navy-800">
                            <span className="text-cyan-300 font-medium">{e.source}</span>
                            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                            <span className="text-emerald-300 font-medium">{e.target}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
