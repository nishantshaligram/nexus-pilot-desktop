<template>
  <div class="ai-summarize-bar">
    <div class="ai-header">
      <div class="ai-title">
        <svg class="sparkle-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M12 2L14.4 7.6L20 10L14.4 12.4L12 18L9.6 12.4L4 10L9.6 7.6L12 2Z"/>
        </svg>
        <span>Summarize with AI:</span>
      </div>
      
      <div class="ai-buttons">
        <a :href="chatGptUrl" target="_blank" rel="noopener noreferrer" class="ai-btn chatgpt" title="Summarize in ChatGPT">
          <span class="icon">🤖</span>
          <span>ChatGPT</span>
        </a>

        <a :href="claudeUrl" target="_blank" rel="noopener noreferrer" class="ai-btn claude" title="Summarize in Claude">
          <span class="icon">🟣</span>
          <span>Claude</span>
        </a>

        <a :href="geminiUrl" target="_blank" rel="noopener noreferrer" class="ai-btn gemini" title="Summarize in Google Gemini">
          <span class="icon">🔷</span>
          <span>Gemini</span>
        </a>

        <a :href="perplexityUrl" target="_blank" rel="noopener noreferrer" class="ai-btn perplexity" title="Search & Summarize in Perplexity">
          <span class="icon">🌐</span>
          <span>Perplexity</span>
        </a>

        <a :href="deepseekUrl" target="_blank" rel="noopener noreferrer" class="ai-btn deepseek" title="Summarize in DeepSeek">
          <span class="icon">🐋</span>
          <span>DeepSeek</span>
        </a>

        <button @click="copyPrompt" class="ai-btn copy-prompt" :class="{ copied: isCopied }" title="Copy Prompt to Clipboard">
          <span>{{ isCopied ? '✓ Copied' : '📋 Copy Prompt' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useData } from 'vitepress'

const { page } = useData()
const currentUrl = ref('https://nishantshaligram.github.io/nexus-pilot-desktop/')
const isCopied = ref(false)

onMounted(() => {
  if (typeof window !== 'undefined') {
    currentUrl.value = window.location.href
  }
})

const promptText = computed(() => {
  const title = page.value.title || 'NexusPilot Documentation'
  return `Please provide a clear, structured summary of this NexusPilot documentation page: "${title}" at ${currentUrl.value}. Focus on key features, architectural design, and developer usage instructions.`
})

const chatGptUrl = computed(() => {
  return `https://chatgpt.com/?q=${encodeURIComponent(promptText.value)}`
})

const claudeUrl = computed(() => {
  return `https://claude.ai/new?q=${encodeURIComponent(promptText.value)}`
})

const geminiUrl = computed(() => {
  return `https://gemini.google.com/app`
})

const perplexityUrl = computed(() => {
  return `https://www.perplexity.ai/search?q=${encodeURIComponent(promptText.value)}`
})

const deepseekUrl = computed(() => {
  return `https://chat.deepseek.com/?q=${encodeURIComponent(promptText.value)}`
})

const copyPrompt = async () => {
  if (typeof navigator !== 'undefined' && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(promptText.value)
      isCopied.value = true
      setTimeout(() => {
        isCopied.value = false
      }, 2500)
    } catch (e) {
      console.error('Failed to copy', e)
    }
  }
}
</script>

<style scoped>
.ai-summarize-bar {
  margin: 1.2rem 0 2rem 0;
  padding: 0.85rem 1.1rem;
  background: var(--vp-c-brand-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.ai-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--vp-c-text-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sparkle-icon {
  color: var(--vp-c-brand-1);
  animation: pulse 2s infinite ease-in-out;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.15); }
}

.ai-buttons {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}

.ai-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.65rem;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  text-decoration: none !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
  line-height: 1.2;
}

.ai-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ai-btn.chatgpt:hover {
  border-color: #10a37f;
  color: #10a37f;
  background: rgba(16, 163, 127, 0.08);
}

.ai-btn.claude:hover {
  border-color: #d97706;
  color: #d97706;
  background: rgba(217, 119, 6, 0.08);
}

.ai-btn.gemini:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
}

.ai-btn.perplexity:hover {
  border-color: #06b6d4;
  color: #06b6d4;
  background: rgba(6, 182, 212, 0.08);
}

.ai-btn.deepseek:hover {
  border-color: #6366f1;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
}

.ai-btn.copy-prompt {
  background: var(--vp-c-brand-soft);
  border-color: var(--vp-c-brand-2);
  color: var(--vp-c-brand-1);
}

.ai-btn.copy-prompt:hover {
  background: var(--vp-c-brand-soft);
  opacity: 0.85;
}

.ai-btn.copy-prompt.copied {
  background: #10b981;
  color: #ffffff;
  border-color: #10b981;
}

@media (max-width: 640px) {
  .ai-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
