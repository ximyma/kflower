/**
 * 数据迁移API
 */
import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// Add auth token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface DBConfig {
  db_type: string
  host?: string
  port?: number
  database: string
  username?: string
  password?: string
}

export interface MigrationRequest {
  source: DBConfig
  target: DBConfig
  tables: string[]
  batch_size: number
  skip_existing: boolean
}

export const testConnection = (config: DBConfig) => {
  return request.post('/migration/test-connection', config)
}

export const getTableInfo = (config: DBConfig, tableName: string) => {
  return request.post('/migration/table-info', { ...config, table_name: tableName })
}

export const executeMigration = (data: MigrationRequest) => {
  return request.post('/migration/execute', data)
}

export const generateScript = (data: MigrationRequest) => {
  return request.post('/migration/generate-script', data)
}
