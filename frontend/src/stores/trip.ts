import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TripPlan } from '../types'

export const useTripStore = defineStore('trip', () => {
    const tripPlan = ref<TripPlan | null>(null)

    function setTripPlan(plan: TripPlan) {
        tripPlan.value = plan
    }

    return { tripPlan, setTripPlan }
})
