<script setup lang="ts">
import { ref } from 'vue'
import StudyAudioPlayer from '../StudyAudioPlayer.vue'

const props = defineProps<{
  referenceAudioUrl: string | null
  userAudioUrl: string | null
}>()

type AudioPlayerHandle = {
  pause: () => void
  jumpTo: (timestamp: number) => Promise<void>
}

const referencePlayer = ref<AudioPlayerHandle | null>(null)
const userPlayer = ref<AudioPlayerHandle | null>(null)

function pauseOtherPlayer(target: 'reference' | 'user') {
  if (target === 'reference') {
    userPlayer.value?.pause()
  } else {
    referencePlayer.value?.pause()
  }
}

async function jumpToUserAudio(timestamp: number) {
  if (!props.userAudioUrl) return
  referencePlayer.value?.pause()
  await userPlayer.value?.jumpTo(timestamp)
}

defineExpose({
  jumpToUserAudio,
  pauseAll: () => {
    referencePlayer.value?.pause()
    userPlayer.value?.pause()
  }
})
</script>

<template>
  <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
    <StudyAudioPlayer
      ref="referencePlayer"
      channel="Left"
      label="原音频"
      :src="referenceAudioUrl"
      hint="用于对照标准读音。"
      @play="pauseOtherPlayer('reference')"
    />

    <StudyAudioPlayer
      ref="userPlayer"
      channel="Right"
      label="用户练习音频"
      :src="userAudioUrl"
      hint="建议里的时间戳会跳到这条录音。"
      @play="pauseOtherPlayer('user')"
    />
  </div>
</template>
