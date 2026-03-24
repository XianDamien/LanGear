<script setup lang="ts">
defineProps<{
  title?: string
}>()
</script>

<template>
  <div
    :class="['bg-brand-panel border border-slate-200 p-4 shadow-mech relative', $attrs.class]"
    v-bind="{ ...$attrs, class: undefined }"
  >
    <div
      v-if="title"
      class="absolute -top-4 left-4 bg-white px-2 text-brand-accent font-bold uppercase tracking-wider text-sm border border-slate-200 flex items-center gap-1 shadow-mech-sm"
    >
      {{ title }}
    </div>
    <slot />
  </div>
</template>

<script lang="ts">
export default { inheritAttrs: false }
</script>
