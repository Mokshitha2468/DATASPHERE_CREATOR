import { AgentLogEvent } from '../types/logs';

export function subscribeLogStream(onEvent: (event: AgentLogEvent) => void): () => void {
  const eventSource = new EventSource('/api/logs/stream');

  eventSource.onmessage = (e) => {
    try {
      const parsed: AgentLogEvent = JSON.parse(e.data);
      if (parsed.type !== 'connected') {
        onEvent(parsed);
      }
    } catch (err) {
      console.warn('Could not parse SSE message:', err);
    }
  };

  eventSource.onerror = (e) => {
    console.debug('SSE disconnected or reconnecting...', e);
  };

  return () => {
    eventSource.close();
  };
}
