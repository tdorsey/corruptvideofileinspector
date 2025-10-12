/**
 * API type definitions matching the backend models
 */

export interface HealthResponse {
  status: string
  version: string
  ffmpeg_available: boolean
}

export enum ScanMode {
  QUICK = 'quick',
  DEEP = 'deep',
  HYBRID = 'hybrid',
}

export enum ScanStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface ScanRequest {
  directory: string
  mode: ScanMode
  recursive: boolean
  max_workers: number
}

export interface ScanResponse {
  scan_id: string
  status: ScanStatus
  message: string
}

export interface ScanProgress {
  processed_count: number
  total_files: number
  current_file?: string
  healthy_count: number
  corrupt_count: number
  suspicious_count: number
  progress_percentage: number
  elapsed_time: number
  estimated_remaining_time?: number
  processing_rate?: number
  phase: string
  scan_mode: string
}

export interface ScanStatusResponse {
  scan_id: string
  status: ScanStatus
  directory: string
  mode: string
  progress: ScanProgress
  results?: ScanResultsData
  error?: string
}

export interface ScanResult {
  file_path: string
  file_name: string
  file_size: number
  is_corrupt: boolean
  confidence: number
  issues: string[]
  scan_mode: string
  scan_time: number
}

export interface ScanSummary {
  total_files: number
  healthy_files: number
  corrupt_files: number
  suspicious_files: number
  total_scan_time: number
  average_scan_time: number
}

export interface ScanResultsData {
  summary: ScanSummary
  details: ScanResult[]
}

export interface ScanResultsResponse {
  scan_id: string
  results: ScanResult[]
  summary: ScanSummary
}

export interface DatabaseStatsResponse {
  total_files: number
  healthy_files: number
  corrupt_files: number
  suspicious_files: number
  last_scan_time?: string
}

export type WebSocketMessage =
  | { type: 'status'; data: ScanStatusResponse }
  | { type: 'progress'; data: ScanProgress }
  | { type: 'complete'; data: ScanResultsData }
  | { type: 'error'; data: { error: string } };
