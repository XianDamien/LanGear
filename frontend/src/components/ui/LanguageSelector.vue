<script setup lang="ts">
const model = defineModel<string>({ default: 'en-zh' })
</script>

<template>
  <div
    class="flex items-center gap-2 bg-brand-light text-slate-800 px-2 py-1 border border-slate-200 shadow-mech-sm"
  >
    <span class="text-xl">🇺🇸/🇨🇳</span>
    <select
      v-model="model"
      class="bg-transparent font-bold outline-none font-sans text-lg uppercase cursor-pointer"
    >
      <option value="en-zh">英语 ➜ 中文</option>
      <option value="fr-zh">法语 ➜ 中文</option>
      <option value="jp-zh">日语 ➜ 中文</option>
    </select>
  </div>
</template>
