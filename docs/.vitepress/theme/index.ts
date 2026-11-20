import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import AiSummarize from './components/AiSummarize.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'doc-before': () => h(AiSummarize)
    })
  },
  enhanceApp({ app }) {
    app.component('AiSummarize', AiSummarize)
  }
}
