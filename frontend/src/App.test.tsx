import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { StatusBadge } from './components/common/StatusBadge';
import { Sidebar } from './components/common/Sidebar';

describe('Frontend Component Tests', () => {
  it('renders StatusBadge with formatted text', () => {
    render(<StatusBadge status="AWAITING_PLAN_APPROVAL" />);
    expect(screen.getByText('AWAITING PLAN APPROVAL')).toBeInTheDocument();
  });

  it('renders Sidebar with brand title', () => {
    render(
      <Sidebar
        currentTab="dashboard"
        onSelectTab={() => {}}
        activeWorkspaceName="My Test Workspace"
      />
    );
    expect(screen.getByText('AETHER')).toBeInTheDocument();
    expect(screen.getByText('ENGINEER')).toBeInTheDocument();
    expect(screen.getByText('My Test Workspace')).toBeInTheDocument();
  });
});

