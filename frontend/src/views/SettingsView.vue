<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSettingsStore } from '@/stores/settings'
import { useDashboardStore } from '@/stores/dashboard'
import RetroCard from '@/components/ui/RetroCard.vue'
import RetroButton from '@/components/ui/RetroButton.vue'

const settingsStore = useSettingsStore()
const dashboardStore = useDashboardStore()
const { dailyNewLimit, dailyReviewLimit, defaultSourceScope, saving, loading } =
  storeToRefs(settingsStore)

onMounted(() => {
  settingsStore.load()
})

async function handleSave() {
  await settingsStore.save()
  await dashboardStore.load()
}
</script>

<template>
  <div class="animate-fadeIn max-w-xl mx-auto">
    <h2 class="text-3xl font-bold mb-6 text-brand-accent uppercase">设置</h2>

    <div v-if="loading" class="text-center text-slate-500 py-20">加载中...</div>

    <template v-else>
      <RetroCard class="space-y-6">
        <div>
          <label class="block text-sm font-bold uppercase text-slate-500 mb-2">
            每日新学数量
          </label>
          <input
            v-model.number="dailyNewLimit"
            type="number"
            min="1"
            max="100"
            class="w-full border border-slate-200 p-2 text-slate-900 font-sans focus:border-brand-accent outline-none"
          />
        </div>

        <div>
          <label class="block text-sm font-bold uppercase text-slate-500 mb-2">
            每日复习数量
          </label>
          <input
            v-model.number="dailyReviewLimit"
            type="number"
            min="1"
            max="200"
            class="w-full border border-slate-200 p-2 text-slate-900 font-sans focus:border-brand-accent outline-none"
          />
        </div>

        <div>
          <label class="block text-sm font-bold uppercase text-slate-500 mb-2">
            默认教材范围
          </label>
          <select
            v-model="defaultSourceScope"
            class="w-full border border-slate-200 p-2 text-slate-900 font-sans focus:border-brand-accent outline-none bg-white"
          >
            <option value="all">全部教材</option>
            <option value="nce">新概念英语</option>
            <option value="ielts">雅思听力</option>
          </select>
        </div>

        <RetroButton
          variant="primary"
          class="w-full"
          :disabled="saving"
          @click="handleSave"
        >
          {{ saving ? '保存中...' : '保存设置' }}
        </RetroButton>
      </RetroCard>
    </template>
  </div>
</template>
