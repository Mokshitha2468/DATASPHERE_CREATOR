import React from 'react';
import { Workspace } from './pages/Workspace';
import { ErrorBoundary } from './components/common/ErrorBoundary';

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Workspace />
    </ErrorBoundary>
  );
};

export default App;
