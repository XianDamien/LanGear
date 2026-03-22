import { ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchSettings, saveSettings } from '@/services/api/settings'
import { ElMessage } from 'element-plus'

export const useSettingsStore = defineStore('settings', () => {
  const dailyNewLimit = ref(10)
  const dailyReviewLimit = ref(30)
  const defaultSourceScope = ref('')
  const saving = ref(false)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const { data } = await fetchSettings()
      dailyNewLimit.value = data.dailyNewLimit
      dailyReviewLimit.value = data.dailyReviewLimit
      defaultSourceScope.value = data.defaultSourceScope
    } finally {
      loading.value = false
    }
  }

  async function save() {
    saving.value = true
    try {
      await saveSettings({
        dailyNewLimit: dailyNewLimit.value,
        dailyReviewLimit: dailyReviewLimit.value,
        defaultSourceScope: defaultSourceScope.value,
      })
      ElMessage.success('设置已保存')
    } catch {
      ElMessage.error('保存失败，请重试')
    } finally {
      saving.value = false
    }
  }

  return {
    dailyNewLimit,
    dailyReviewLimit,
    defaultSourceScope,
    saving,
    loading,
    load,
    save,
  }
})
