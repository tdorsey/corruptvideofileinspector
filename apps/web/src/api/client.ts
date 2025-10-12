const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ScanRequest {
  directory: string;
  scan_mode?: 'quick' | 'deep' | 'hybrid';
  recursive?: boolean;
  resume?: boolean;
}

export interface ScanResponse {
  id: string;
  directory: string;
  scan_mode: string;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  results_count: number;
}

export interface ProgressUpdate {
  current_file: string;
  processed_files: number;
  total_files: number;
  progress_percentage: number;
  corrupt_count: number;
  healthy_count: number;
  status?: string;
  error?: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async createScan(request: ScanRequest): Promise<ScanResponse> {
    const response = await fetch(`${this.baseUrl}/api/scans`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to create scan: ${error}`);
    }

    return response.json();
  }

  async listScans(): Promise<ScanResponse[]> {
    const response = await fetch(`${this.baseUrl}/api/scans`);

    if (!response.ok) {
      throw new Error('Failed to fetch scans');
    }

    return response.json();
  }

  async getScan(scanId: string): Promise<ScanResponse> {
    const response = await fetch(`${this.baseUrl}/api/scans/${scanId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch scan');
    }

    return response.json();
  }

  connectWebSocket(
    scanId: string,
    onMessage: (update: ProgressUpdate) => void,
    onError?: (error: Event) => void
  ): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/scans/${scanId}`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      onMessage(update);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) {
        onError(error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return ws;
  }
}

export const apiClient = new ApiClient();
