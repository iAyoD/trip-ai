import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Result from '../views/Result.vue'

const routes = [
    {
        path: '/',
        name: 'home',
        component: Home
    },
    {
        path: '/result',
        name: 'result',
        component: Result
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
