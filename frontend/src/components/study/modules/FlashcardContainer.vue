<script setup lang="ts">
import { computed } from 'vue'
import RetroCard from '@/components/ui/RetroCard.vue'

const props = defineProps<{
  isFlipped: boolean
}>()

const cardClass = computed(() =>
  props.isFlipped
    ? 'flex h-full min-h-0 flex-col overflow-hidden p-4 sm:p-6 lg:p-8 transition-all duration-300'
    : 'flex h-full min-h-0 flex-col items-center justify-center p-6 text-center sm:p-8 transition-all duration-300',
)
</script>

<template>
  <RetroCard :class="cardClass">
    <div
      v-if="!isFlipped"
      class="w-full flex flex-col items-center justify-center"
      data-testid="card-front-container"
    >
      <slot name="front" />
    </div>
    <div
      v-else
      class="flex h-full min-h-0 w-full flex-col text-left animate-fadeIn"
      data-testid="card-back-container"
    >
      <slot name="back" />
    </div>
  </RetroCard>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fadeIn {
  animation: fadeIn 0.4s ease-out;
}
</style>
