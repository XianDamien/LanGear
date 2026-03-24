<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'success'
  size?: 'sm' | 'md' | 'lg'
  icon?: Component
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
})

const baseStyle =
  'inline-flex min-w-0 select-none items-center justify-center gap-2 border-2 font-sans uppercase tracking-[0.14em] transition-all duration-150 active:translate-y-1 active:shadow-none disabled:translate-y-0 disabled:cursor-not-allowed disabled:shadow-none disabled:opacity-55 [&>svg]:shrink-0'

const variants: Record<string, string> = {
  primary:
    'bg-brand-accent border-brand-accent-hover text-white font-bold shadow-mech hover:bg-brand-accent-hover',
  secondary:
    'bg-brand-light border-slate-200 text-slate-700 shadow-mech hover:border-slate-300 hover:bg-slate-50',
  danger:
    'bg-brand-alert border-red-600 text-white shadow-mech hover:bg-red-500',
  success:
    'bg-emerald-600 border-emerald-700 text-white shadow-mech hover:bg-emerald-500',
  ghost:
    'border-transparent bg-transparent text-slate-500 hover:border-slate-200 hover:bg-white/80 hover:text-slate-900 shadow-none',
}

const sizes: Record<string, string> = {
  sm: 'min-h-[3rem] px-3 py-2 text-sm',
  md: 'min-h-[3.5rem] px-4 py-2.5 text-lg',
  lg: 'min-h-[4rem] px-6 py-3 text-xl font-bold',
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
