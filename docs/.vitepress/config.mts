import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/NexusPilot/',
  title: 'NexusPilot',
  description: 'Universal Desktop Computer-Use MCP Suite & Antigravity Plugin',

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/NexusPilot/assets/logo.svg' }],
    ['meta', { name: 'author', content: 'Nishant Shaligram' }],
    ['meta', { name: 'keywords', content: 'computer use, mcp, model context protocol, windows automation, ai agent, desktop automation, claude code, cursor ide, antigravity, uia, win32 sendinput, rpa, python' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'NexusPilot - Universal Desktop Computer-Use MCP Suite' }],
    ['meta', { property: 'og:description', content: 'Empower AI coding agents with human-grade vision, mouse actuation, keyboard input, and Windows UI Automation control.' }],
    ['meta', { property: 'og:image', content: 'https://nishantshaligram.github.io/NexusPilot/assets/brand_logo.jpg' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:image', content: 'https://nishantshaligram.github.io/NexusPilot/assets/brand_logo.jpg' }],
    [
      'script',
      { type: 'application/ld+json' },
      JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        name: 'NexusPilot',
        operatingSystem: 'Windows 10, Windows 11',
        applicationCategory: 'DeveloperApplication',
        description: 'Universal Desktop Computer-Use MCP Suite and Antigravity Plugin providing AI agents with human-like vision, mouse control, keyboard input, and Windows UI Automation perception.',
        url: 'https://nishantshaligram.github.io/NexusPilot/',
        downloadUrl: 'https://github.com/nishantshaligram/NexusPilot',
        softwareVersion: '1.0.0',
        license: 'https://www.apache.org/licenses/LICENSE-2.0',
        author: {
          '@type': 'Person',
          name: 'Nishant Shaligram'
        }
      })
    ]
  ],

  themeConfig: {
    logo: '/assets/logo.svg',
    siteTitle: 'NexusPilot',

    search: {
      provider: 'local'
    },

    nav: [
      { text: 'Home', link: '/' },
      { text: 'Quickstart', link: '/getting-started/quickstart' },
      { text: 'Architecture', link: '/architecture/dual-modal' },
      { text: 'Integrations', link: '/integrations/antigravity' },
      { text: 'Tools Reference', link: '/reference/mcp-tools' }
    ],

    sidebar: [
      {
        text: 'Getting Started',
        collapsed: false,
        items: [
          { text: 'Overview', link: '/' },
          { text: 'Installation', link: '/getting-started/installation' },
          { text: 'Quickstart Guide', link: '/getting-started/quickstart' }
        ]
      },
      {
        text: 'Architecture & Engineering',
        collapsed: false,
        items: [
          { text: 'Dual-Modal Perception', link: '/architecture/dual-modal' },
          { text: 'Win32 Actuation & Kinematics', link: '/architecture/actuation' },
          { text: 'Safety Guardian & Failsafes', link: '/architecture/safety' }
        ]
      },
      {
        text: 'Agent Integrations',
        collapsed: false,
        items: [
          { text: 'Google Antigravity', link: '/integrations/antigravity' },
          { text: 'Claude (Code & Desktop)', link: '/integrations/claude' },
          { text: 'Cursor & Windsurf', link: '/integrations/cursor' }
        ]
      },
      {
        text: 'API & Reference',
        collapsed: false,
        items: [
          { text: 'MCP Tool Catalog', link: '/reference/mcp-tools' },
          { text: 'Supported Shortcuts', link: '/reference/shortcuts' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/nishantshaligram/NexusPilot' }
    ],

    footer: {
      message: 'Released under the Apache 2.0 License.',
      copyright: 'Copyright © 2026 Nishant Shaligram'
    }
  }
})
