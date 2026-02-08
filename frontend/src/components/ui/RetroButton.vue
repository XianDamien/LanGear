<script setup lang="ts">
import type { Component } from 'vue'

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
  'font-sans uppercase tracking-wide border-2 transition-all active:translate-y-1 active:shadow-none flex items-center justify-center gap-2'

const variants: Record<string, string> = {
  primary:
    'bg-brand-accent border-brand-accent-hover text-white font-bold shadow-mech hover:bg-brand-accent-hover',
  secondary:
    'bg-brand-light border-slate-200 text-slate-700 shadow-mech hover:border-slate-300',
  danger:
    'bg-brand-alert border-red-600 text-white shadow-mech hover:bg-red-500',
  ghost:
    'bg-transparent border-transparent text-slate-700 hover:text-slate-900 shadow-none border-0',
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
    :class="[baseStyle, variants[props.variant], sizes[props.size], $attrs.class]"
    v-bind="{ ...$attrs, class: undefined }"
  >
    <component :is="props.icon" v-if="props.icon" :size="iconSizes[props.size]" />
    <slot />
  </button>
</template>

<script lang="ts">
export default { inheritAttrs: false }
</script>
