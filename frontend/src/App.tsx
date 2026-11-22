import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './services/api';
import { Workspace, Task } from './types';
import { Sidebar } from './components/common/Sidebar';
import { Header } from './components/common/Header';

import { Dashboard } from './pages/Dashboard';
import { WorkspacesPage } from './pages/WorkspacesPage';
import { RepoExplorerPage } from './pages/RepoExplorerPage';
import { TaskConsolePage } from './pages/TaskConsolePage';
import { PlanningPage } from './pages/PlanningPage';
import { DiffReviewPage } from './pages/DiffReviewPage';
import { TestResultsPage } from './pages/TestResultsPage';
import { EvaluationLabPage } from './pages/EvaluationLabPage';
import { SettingsPage } from './pages/SettingsPage';

export const AppContent: React.FC = () => {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | undefined>(undefined);
  const queryClient = useQueryClient();

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 10000,
  });

  const { data: workspaces = [] } = useQuery({
    queryKey: ['workspaces'],
    queryFn: () => api.getWorkspaces(),
  });

  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks', activeWorkspace?.id],
    queryFn: () => api.getTasks(activeWorkspace?.id),
    refetchInterval: 3000,
  });

  // Set default active workspace if none selected
  useEffect(() => {
    if (!activeWorkspace && workspaces.length > 0) {
      setActiveWorkspace(workspaces[0]);
    }
  }, [workspaces, activeWorkspace]);

  const activeTask = tasks[0];

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
    queryClient.invalidateQueries({ queryKey: ['health'] });
  };

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return (
          <Dashboard
            health={health}
            workspaces={workspaces}
            tasks={tasks}
            activeWorkspace={activeWorkspace}
            onNavigate={setCurrentTab}
          />
        );
      case 'workspaces':
        return (
          <WorkspacesPage
            workspaces={workspaces}
            activeWorkspace={activeWorkspace}
            onSelectWorkspace={setActiveWorkspace}
            onRefresh={handleRefresh}
          />
        );
      case 'repo-explorer':
        return <RepoExplorerPage activeWorkspace={activeWorkspace} />;
      case 'task-console':
        return (
          <TaskConsolePage
            tasks={tasks}
            activeWorkspace={activeWorkspace}
            onRefresh={handleRefresh}
            onNavigate={setCurrentTab}
          />
        );
      case 'planning':
        return <PlanningPage activeTask={activeTask} onRefresh={handleRefresh} />;
      case 'diff-review':
        return <DiffReviewPage activeTask={activeTask} onRefresh={handleRefresh} />;
      case 'test-results':
        return <TestResultsPage activeTask={activeTask} />;
      case 'evaluation':
        return <EvaluationLabPage />;
      case 'settings':
        return <SettingsPage health={health} onRefresh={handleRefresh} />;
      default:
        return (
          <Dashboard
            health={health}
            workspaces={workspaces}
            tasks={tasks}
            activeWorkspace={activeWorkspace}
            onNavigate={setCurrentTab}
          />
        );
    }
  };

  return (
    <div className="flex h-screen bg-navy-950 text-slate-100 overflow-hidden font-sans">
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        activeWorkspaceName={activeWorkspace?.name}
      />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          health={health}
          workspaces={workspaces}
          activeWorkspace={activeWorkspace}
          onSelectWorkspace={setActiveWorkspace}
        />
        <main className="flex-1 overflow-y-auto bg-navy-950">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

