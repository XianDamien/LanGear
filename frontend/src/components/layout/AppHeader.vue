<script setup lang="ts">
import { Menu, X, Plus } from 'lucide-vue-next'
import LanguageSelector from '../ui/LanguageSelector.vue'
import RetroButton from '../ui/RetroButton.vue'

defineProps<{
  mobileMenuOpen: boolean
}>()

const emit = defineEmits<{
  toggleMenu: []
}>()

const langPair = defineModel<string>('langPair', { default: 'en-zh' })
</script>

<template>
  <header
    class="h-20 border-b border-slate-200 bg-brand-panel flex items-center justify-between px-6 sticky top-0 z-40 shadow-mech-sm"
  >
    <button class="md:hidden text-slate-900" @click="emit('toggleMenu')">
      <component :is="mobileMenuOpen ? X : Menu" />
    </button>

    <div class="hidden md:block text-slate-500 uppercase text-sm">
      流利学习引擎
    </div>

    <div class="flex items-center gap-4">
      <LanguageSelector v-model="langPair" />
      <RetroButton variant="secondary" size="sm" :icon="Plus" />
    </div>
  </header>
</template>
