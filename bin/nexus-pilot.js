#!/usr/bin/env node

import { startMcpServer } from '../src/server-runner.js';
import { runInstaller } from '../src/installer.js';
import { runDoctor } from '../src/doctor.js';

const args = process.argv.slice(2);
const command = args[0]?.toLowerCase();

function printHelp() {
  console.log(`
NexusPilot - Universal Desktop Computer-Use MCP Suite

Usage:
  npx nexus-pilot                          Start the MCP server daemon over stdio (default)
  npx nexus-pilot serve                    Explicitly run the MCP server daemon
  npx nexus-pilot install [options]        Install plugin & skills into AI agent configs
  npx nexus-pilot doctor                   Run environment & accessibility diagnostics
  npx nexus-pilot --help                   Show this help message
  npx nexus-pilot --version                Show package version

Install Options:
  --agent <name>       Target agent to configure: all, antigravity, claude, cursor, windsurf
  --ide <name>         Alias for --agent (e.g. --ide cursor)

Examples:
  npx nexus-pilot install
  npx nexus-pilot install --agent antigravity
  npx nexus-pilot install --ide claude
  npx nexus-pilot doctor
`);
}

function parseFlag(flagName) {
  const idx = args.indexOf(flagName);
  if (idx !== -1 && args[idx + 1] && !args[idx + 1].startsWith('-')) {
    return args[idx + 1];
  }
  const inline = args.find(a => a.startsWith(`${flagName}=`));
  if (inline) {
    return inline.split('=')[1];
  }
  return null;
}

switch (command) {
  case 'install': {
    const target = parseFlag('--agent') || parseFlag('--ide');
    await runInstaller(target);
    break;
  }
  case 'doctor':
    runDoctor();
    break;
  case 'serve':
    startMcpServer();
    break;
  case '--help':
  case '-h':
  case 'help':
    printHelp();
    break;
  case '--version':
  case '-v':
    console.log('nexus-pilot v1.0.0');
    break;
  default:
    // When invoked with no args or unrecognized flag, start the MCP server directly
    startMcpServer();
    break;
}
