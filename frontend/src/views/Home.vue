<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '../services/api'
import type { TripPlanRequest } from '../types'
import { useTripStore } from '../stores/trip'
import { MapPin, Wallet, ArrowRight, CheckCircle, Map, Sparkles } from 'lucide-vue-next'
import { Dayjs } from 'dayjs'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

// Date range for the picker
const dateRange = ref<[Dayjs, Dayjs] | undefined>(undefined)

const formData = ref<TripPlanRequest>({
  city: '',
  start_date: '',
  end_date: '',
  days: 3,
  preferences: '历史文化',
  budget: '中等',
  transportation: '公共交通',
  accommodation: '经济型酒店'
})

// Auto-calculate days when dates change
watch(dateRange, (newRange) => {
    if (newRange && newRange.length === 2) {
        const start = newRange[0]
        const end = newRange[1]
        formData.value.start_date = start.format('YYYY-MM-DD')
        formData.value.end_date = end.format('YYYY-MM-DD')
        
        // Calculate difference in days (inclusive)
        const diff = end.diff(start, 'day') + 1
        formData.value.days = diff
    }
})

const handleSubmit = async () => {
  if (!formData.value.city) {
      message.error('请输入目的地城市')
      return
  }
  if (!dateRange.value) {
      message.error('请选择旅行日期')
      return
  }

  loading.value = true
  loadingProgress.value = 0
  
  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += 10
      if (loadingProgress.value <= 30) loadingStatus.value = '🔍 正在搜索景点...'
      else if (loadingProgress.value <= 50) loadingStatus.value = '🌤️ 正在查询天气...'
      else if (loadingProgress.value <= 70) loadingStatus.value = '🏨 正在推荐酒店...'
      else loadingStatus.value = '📋 正在生成行程计划...'
    }
  }, 500)
  
  try {
    const response = await generateTripPlan(formData.value)
    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成！'
    
    // Save to Pinia (optional now but good for consistency)
    const tripStore = useTripStore()
    tripStore.setTripPlan(response)
    
    // Save to sessionStorage for the new Result.vue
    sessionStorage.setItem('tripPlan', JSON.stringify(response))
    
    setTimeout(() => {
        router.push({ name: 'result' })
    }, 500)
  } catch (error) {
    clearInterval(progressInterval)
    message.error('生成计划失败,请重试')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const scrollToForm = () => {
    document.getElementById('planner-form')?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 font-sans">
    <!-- Navigation -->
    <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        <div class="flex items-center space-x-2">
            <Sparkles class="w-8 h-8 text-indigo-600" />
            <span class="text-xl font-bold tracking-tight">TripAI</span>
        </div>
        <div class="hidden md:flex space-x-8">
            <a href="#features" class="text-slate-600 hover:text-indigo-600 transition-colors">功能</a>
            <a href="#planner-form" class="text-slate-600 hover:text-indigo-600 transition-colors">开始规划</a>
        </div>
    </nav>

    <!-- Hero Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
            <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-6">
                智能规划您的<br>
                <span class="text-indigo-600">完美旅程</span>
            </h1>
            <p class="text-lg md:text-xl text-slate-600 mb-8 leading-relaxed max-w-lg">
                告别繁琐的攻略制作。只需几秒钟，AI 为您生成包含景点、美食、酒店的个性化行程方案。
            </p>
            <div class="flex flex-col sm:flex-row gap-4">
                <button @click="scrollToForm" class="px-8 py-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2">
                    立即开始
                    <ArrowRight class="w-5 h-5" />
                </button>
                <button class="px-8 py-4 bg-white text-slate-700 font-semibold rounded-lg border border-slate-200 hover:border-indigo-600 hover:text-indigo-600 transition-all flex items-center justify-center">
                    了解更多
                </button>
            </div>
        </div>
        
        <!-- Right Side Placeholder / Form Container -->
        <div class="relative">
            <div class="absolute -inset-4 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl opacity-20 blur-2xl animate-pulse"></div>
            <div id="planner-form" class="relative bg-white rounded-2xl shadow-xl p-8 border border-slate-100">
                <div class="flex items-center gap-3 mb-6">
                    <div class="p-2 bg-indigo-50 rounded-lg">
                        <MapPin class="w-6 h-6 text-indigo-600" />
                    </div>
                    <h3 class="text-xl font-bold">定制您的行程</h3>
                </div>

                <a-form :model="formData" @finish="handleSubmit" layout="vertical">
                    <a-form-item label="目的地" name="city" class="mb-4">
                        <a-input v-model:value="formData.city" placeholder="例如：北京、上海、东京" size="large" class="rounded-lg" />
                    </a-form-item>

                    <a-form-item label="旅行日期" class="mb-4">
                        <a-range-picker v-model:value="dateRange" size="large" style="width: 100%" class="rounded-lg" />
                    </a-form-item>

                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <a-form-item label="天数">
                            <a-input-number v-model:value="formData.days" disabled size="large" style="width: 100%" class="rounded-lg bg-slate-50" />
                        </a-form-item>
                        <a-form-item label="预算">
                            <a-select v-model:value="formData.budget" size="large" class="rounded-lg">
                                <a-select-option value="经济">经济</a-select-option>
                                <a-select-option value="中等">中等</a-select-option>
                                <a-select-option value="豪华">豪华</a-select-option>
                            </a-select>
                        </a-form-item>
                    </div>

                    <a-form-item label="偏好" class="mb-6">
                        <a-input v-model:value="formData.preferences" placeholder="例如：历史文化、自然风光" size="large" class="rounded-lg" />
                    </a-form-item>

                    <a-button type="primary" html-type="submit" size="large" :loading="loading" block class="h-12 bg-indigo-600 hover:bg-indigo-700 border-none rounded-lg text-lg font-semibold shadow-md">
                        {{ loading ? '正在规划中...' : '生成行程方案' }}
                    </a-button>

                    <div v-if="loading" class="mt-4">
                        <a-progress :percent="loadingProgress" :stroke-color="{ '0%': '#4f46e5', '100%': '#818cf8' }" />
                        <p class="text-center text-sm text-slate-500 mt-2">{{ loadingStatus }}</p>
                    </div>
                </a-form>
            </div>
        </div>
    </div>

    <!-- Feature Section -->
    <div id="features" class="bg-white py-24">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-3xl font-bold text-slate-900 mb-4">为什么选择 TripAI？</h2>
                <p class="text-lg text-slate-600 max-w-2xl mx-auto">我们利用最先进的 AI 技术，为您提供传统旅行社无法比拟的个性化服务。</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-12">
                <!-- Feature 1 -->
                <div class="p-8 bg-slate-50 rounded-2xl hover:shadow-lg transition-shadow duration-300">
                    <div class="w-14 h-14 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
                        <Map class="w-8 h-8 text-indigo-600" />
                    </div>
                    <h3 class="text-xl font-bold mb-3">智能路线规划</h3>
                    <p class="text-slate-600 leading-relaxed">
                        自动优化景点游览顺序，减少路途奔波。结合地图数据，为您规划最合理的每日路线。
                    </p>
                </div>

                <!-- Feature 2 -->
                <div class="p-8 bg-slate-50 rounded-2xl hover:shadow-lg transition-shadow duration-300">
                    <div class="w-14 h-14 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
                        <Wallet class="w-8 h-8 text-indigo-600" />
                    </div>
                    <h3 class="text-xl font-bold mb-3">精准预算控制</h3>
                    <p class="text-slate-600 leading-relaxed">
                        根据您的预算范围，自动推荐合适的酒店和餐饮。实时计算门票和交通费用，让每一分钱都花在刀刃上。
                    </p>
                </div>

                <!-- Feature 3 -->
                <div class="p-8 bg-slate-50 rounded-2xl hover:shadow-lg transition-shadow duration-300">
                    <div class="w-14 h-14 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
                        <CheckCircle class="w-8 h-8 text-indigo-600" />
                    </div>
                    <h3 class="text-xl font-bold mb-3">完全个性化</h3>
                    <p class="text-slate-600 leading-relaxed">
                        无论是亲子游、情侣游还是独自旅行，只需输入您的偏好，AI 就能为您量身定制独一无二的行程。
                    </p>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
/* Override Ant Design styles to match Tailwind theme */
:deep(.ant-input-lg), :deep(.ant-select-selector), :deep(.ant-picker-large) {
    border-radius: 0.5rem !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
}

:deep(.ant-btn-primary) {
    background-color: #4f46e5;
    border-color: #4f46e5;
}

:deep(.ant-btn-primary:hover) {
    background-color: #4338ca !important;
    border-color: #4338ca !important;
}
</style>
