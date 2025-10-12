/**
 * API service for communicating with the backend
 */

import axios, { AxiosInstance } from 'axios'
import {
  HealthResponse,
  ScanRequest,
  ScanResponse,
  ScanStatusResponse,
  ScanResultsResponse,
  DatabaseStatsResponse,
} from '@/types/api'

class ApiService {
  private client: AxiosInstance

  constructor(baseURL: string = '') {
    this.client = axios.create({
      baseURL: baseURL || '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health')
    return response.data
  }

  async startScan(request: ScanRequest): Promise<ScanResponse> {
    const response = await this.client.post<ScanResponse>('/scans', request)
    return response.data
  }

  async getScanStatus(scanId: string): Promise<ScanStatusResponse> {
    const response = await this.client.get<ScanStatusResponse>(`/scans/${scanId}`)
    return response.data
  }

  async getScanResults(scanId: string): Promise<ScanResultsResponse> {
    const response = await this.client.get<ScanResultsResponse>(`/scans/${scanId}/results`)
    return response.data
  }

  async cancelScan(scanId: string): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/scans/${scanId}`)
    return response.data
  }

  async getDatabaseStats(): Promise<DatabaseStatsResponse> {
    const response = await this.client.get<DatabaseStatsResponse>('/database/stats')
    return response.data
  }

  createWebSocket(scanId: string): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return new WebSocket(`${protocol}//${host}/ws/scans/${scanId}`)
  }
}

export const apiService = new ApiService()
