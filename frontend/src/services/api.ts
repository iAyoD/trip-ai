import axios from 'axios'
import type { TripPlanRequest, TripPlan } from '../types'

const api = axios.create({
    baseURL: 'http://localhost:8000/api',
    timeout: 1200000, // 20 minutes timeout
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request interceptor
api.interceptors.request.use(
    config => {
        console.log('Sending request:', config)
        return config
    },
    error => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
    response => {
        console.log('Received response:', response)
        return response
    },
    error => {
        console.error('Request failed:', error)
        return Promise.reject(error)
    }
)

// Generate trip plan
export const generateTripPlan = async (request: TripPlanRequest): Promise<TripPlan> => {
    const response = await api.post<TripPlan>('/trip/plan', request)
    return response.data
}
