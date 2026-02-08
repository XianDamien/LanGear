<script setup lang="ts">
import type { Component } from 'vue'
import { useRoute } from 'vue-router'

defineProps<{
  to: string
  icon: Component
  label: string
}>()

defineEmits<{
  navigate: []
}>()

const route = useRoute()
</script>

<template>
  <router-link :to="to" @click="$emit('navigate')">
    <div
      :class="[
        'group flex items-center gap-3 px-4 py-3 mb-2 transition-all cursor-pointer border-l-4',
        route.path === to
          ? 'bg-red-50 border-brand-accent'
          : 'border-transparent hover:bg-slate-50',
      ]"
    >
      <component
        :is="icon"
        :size="24"
        :class="
          route.path === to
            ? 'text-brand-accent'
            : 'text-slate-400 group-hover:text-brand-accent'
        "
      />
      <span
        :class="[
          'uppercase tracking-widest text-lg',
          route.path === to
            ? 'text-slate-900'
            : 'text-slate-600 group-hover:text-slate-900',
        ]"
      >
        {{ label }}
      </span>
    </div>
  </router-link>
</template>
