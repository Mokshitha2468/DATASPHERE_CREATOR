import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#080c14] text-slate-100 flex items-center justify-center p-6">
          <div className="max-w-xl w-full bg-slate-900/90 border border-rose-500/40 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
            <div className="flex items-center gap-3 text-rose-400 mb-4">
              <div className="p-3 bg-rose-500/10 rounded-xl border border-rose-500/30">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-100">Application Error</h2>
                <p className="text-xs text-slate-400">An unexpected UI exception occurred.</p>
              </div>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-rose-300 overflow-auto max-h-48 mb-5">
              <div className="font-bold mb-1">{this.state.error?.name}: {this.state.error?.message}</div>
              {this.state.error?.stack && (
                <pre className="text-[10px] text-slate-500 whitespace-pre-wrap">{this.state.error.stack}</pre>
              )}
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors"
              >
                Try to Recover
              </button>
              <button
                onClick={this.handleReload}
                className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 text-xs font-bold rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-sky-500/20"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
