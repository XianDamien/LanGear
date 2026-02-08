<script setup lang="ts">
const leaders = [
  { rank: 1, name: 'Polyglot_99', points: 9950, isUser: false },
  { rank: 2, name: '你', points: 1240, isUser: true },
  { rank: 3, name: 'Learner_X', points: 800, isUser: false },
]
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-4 uppercase text-brand-accent">排行榜</h2>
    <div class="bg-white p-4 border border-slate-200 shadow-mech-sm">
      <div
        v-for="(leader, idx) in leaders"
        :key="leader.rank"
        :class="[
          'flex justify-between pb-2 mb-2',
          idx < leaders.length - 1 ? 'border-b border-slate-200' : '',
          leader.isUser ? 'bg-red-50 px-2 -mx-2' : '',
          !leader.isUser && idx === leaders.length - 1 ? 'text-slate-500' : '',
        ]"
      >
        <span>
          <span class="font-pixel text-brand-accent">{{ leader.rank }}</span>.
          {{ leader.name }}
        </span>
        <span :class="leader.isUser ? 'text-slate-900 font-bold' : 'text-brand-accent'">
          <span class="font-pixel text-brand-accent">{{ leader.points }}</span>
          积分
        </span>
      </div>
    </div>
  </div>
</template>
