<script setup lang="ts">
import type { Component } from 'vue'

defineOptions({
  inheritAttrs: false,
})

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  icon?: Component
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
})

const baseStyle =
  'font-sans uppercase tracking-wide border-2 transition-all active:translate-y-1 active:shadow-none flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none'

const variants: Record<string, string> = {
  primary:
    'bg-brand-accent border-brand-accent-hover text-white font-bold shadow-mech hover:bg-brand-accent-hover disabled:hover:bg-brand-accent disabled:hover:border-brand-accent-hover',
  secondary:
    'bg-brand-light border-slate-200 text-slate-700 shadow-mech hover:border-slate-300 disabled:hover:border-slate-200 disabled:hover:bg-brand-light',
  danger:
    'bg-brand-alert border-red-600 text-white shadow-mech hover:bg-red-500 disabled:hover:bg-brand-alert disabled:hover:border-red-600',
  ghost:
    'bg-transparent border-transparent text-slate-700 hover:text-slate-900 shadow-none border-0 disabled:hover:text-slate-700',
}

const sizes: Record<string, string> = {
  sm: 'px-2 py-1 text-sm',
  md: 'px-4 py-2 text-lg',
  lg: 'px-6 py-3 text-xl font-bold',
}

const iconSizes: Record<string, number> = {
  sm: 16,
  md: 20,
  lg: 24,
}
</script>

<template>
  <button
    type="button"
    :class="[baseStyle, variants[props.variant], sizes[props.size], $attrs.class]"
    v-bind="{ ...$attrs, class: undefined }"
  >
    <component :is="props.icon" v-if="props.icon" :size="iconSizes[props.size]" />
    <slot />
  </button>
</template>
