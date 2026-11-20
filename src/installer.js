import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function getHomeDir() {
  return os.homedir();
}

function copyFolderRecursive(source, target) {
  if (!fs.existsSync(target)) {
    fs.mkdirSync(target, { recursive: true });
  }

  const files = fs.readdirSync(source);
  for (const file of files) {
    const curSource = path.join(source, file);
    const curTarget = path.join(target, file);

    if (fs.lstatSync(curSource).isDirectory()) {
      copyFolderRecursive(curSource, curTarget);
    } else {
      fs.copyFileSync(curSource, curTarget);
    }
  }
}

function updateMcpJson(filePath, serverDef, agentName) {
  try {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    let config = {};
    if (fs.existsSync(filePath)) {
      try {
        const raw = fs.readFileSync(filePath, 'utf-8').trim();
        if (raw) {
          config = JSON.parse(raw);
        }
      } catch (err) {
        console.warn(`  [!] Warning: Existing config at ${filePath} was malformed. Recreating safely.`);
        config = {};
      }
    }

    if (!config.mcpServers) {
      config.mcpServers = {};
    }

    config.mcpServers['nexus-pilot'] = serverDef;

    fs.writeFileSync(filePath, JSON.stringify(config, null, 2), 'utf-8');
    console.log(`  \x1b[32m[✓]\x1b[0m Configured \x1b[1m${agentName}\x1b[0m successfully!`);
    console.log(`      \x1b[90mLocation: ${filePath}\x1b[0m`);
    return true;
  } catch (err) {
    console.error(`  \x1b[31m[✗]\x1b[0m Failed to configure ${agentName}: ${err.message}`);
    return false;
  }
}

export function runInstaller(targetAgent = 'all') {
  const home = getHomeDir();
  const projectRoot = path.resolve(__dirname, '..');
  const serverPath = path.join(projectRoot, 'nexus-pilot', 'server', 'pilot_server.py').replace(/\\/g, '/');
  const pluginSourceDir = path.join(projectRoot, 'nexus-pilot');

  const normalizedTarget = targetAgent.toLowerCase();

  const mcpServerDef = {
    command: 'python',
    args: [serverPath],
    description: 'NexusPilot Windows Desktop Computer-Use Engine'
  };

  console.log('\n\x1b[36m=======================================================');
  console.log('   NexusPilot Universal Agent MCP & Plugin Installer   ');
  console.log('=======================================================\x1b[0m');
  console.log(`Target: \x1b[1m${targetAgent}\x1b[0m\n`);

  // 1. Antigravity
  if (normalizedTarget === 'all' || normalizedTarget === 'antigravity') {
    console.log('\x1b[36m[1] Installing for Google Antigravity...\x1b[0m');
    const pluginTargetDir = path.join(home, '.gemini', 'config', 'plugins', 'nexus-pilot');
    try {
      copyFolderRecursive(pluginSourceDir, pluginTargetDir);
      console.log(`  \x1b[32m[✓]\x1b[0m Plugin & Skills installed in: \x1b[90m${pluginTargetDir}\x1b[0m`);

      const agyMcpPath = path.join(home, '.gemini', 'antigravity', 'mcp_config.json');
      updateMcpJson(agyMcpPath, mcpServerDef, 'Antigravity Global MCP');
    } catch (err) {
      console.error(`  \x1b[31m[✗]\x1b[0m Antigravity installation error: ${err.message}`);
    }
  }

  // 2. Claude (Claude Code CLI & Desktop)
  if (normalizedTarget === 'all' || normalizedTarget === 'claude' || normalizedTarget === 'claude-code') {
    console.log('\n\x1b[36m[2] Installing for Claude (Code & Desktop)...\x1b[0m');
    const claudeCodePath = path.join(home, '.claude.json');
    updateMcpJson(claudeCodePath, mcpServerDef, 'Claude Code CLI');

    const appData = process.env.APPDATA || path.join(home, 'AppData', 'Roaming');
    const claudeDesktopPath = path.join(appData, 'Claude', 'claude_desktop_config.json');
    updateMcpJson(claudeDesktopPath, mcpServerDef, 'Claude Desktop App');
  }

  // 3. Cursor
  if (normalizedTarget === 'all' || normalizedTarget === 'cursor') {
    console.log('\n\x1b[36m[3] Installing for Cursor IDE...\x1b[0m');
    const cursorMcpPath = path.join(home, '.cursor', 'mcp.json');
    updateMcpJson(cursorMcpPath, mcpServerDef, 'Cursor Global MCP');
  }

  // 4. Windsurf
  if (normalizedTarget === 'all' || normalizedTarget === 'windsurf') {
    console.log('\n\x1b[36m[4] Installing for Windsurf / Codeium...\x1b[0m');
    const windsurfPath = path.join(home, '.codeium', 'windsurf', 'mcp_config.json');
    updateMcpJson(windsurfPath, mcpServerDef, 'Windsurf Global MCP');
  }

  console.log('\n\x1b[36m=======================================================');
  console.log('   \x1b[32mInstallation Complete!\x1b[36m NexusPilot is ready to use.   ');
  console.log('=======================================================\x1b[0m');
  console.log('Restart your AI agent or reload your editor window to activate the tools.\n');
}
