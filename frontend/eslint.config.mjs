import pluginVue from 'eslint-plugin-vue'
import {
  configureVueProject,
  defineConfigWithVueTs,
  vueTsConfigs,
} from '@vue/eslint-config-typescript'

configureVueProject({
  rootDir: import.meta.dirname,
})

export default defineConfigWithVueTs(
  {
    name: 'app/ignores',
    ignores: ['dist', 'coverage', 'playwright-report', 'test-results'],
  },
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
  {
    files: ['**/*.{ts,vue}'],
    rules: {
      'vue/multi-word-component-names': 'off',
    },
  },
)
