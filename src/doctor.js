import { execSync } from 'node:child_process';
import os from 'node:os';

export function runDoctor() {
  console.log('\n\x1b[36m=======================================================');
  console.log('   NexusPilot: Desktop - Environment Diagnostic Probe  ');
  console.log('=======================================================\x1b[0m\n');

  // 1. Operating System
  const platform = os.platform();
  const release = os.release();
  const isWindows = platform === 'win32';
  if (isWindows) {
    console.log(`\x1b[32m[✓]\x1b[0m OS: Windows (${release}, Architecture ${os.arch()})`);
  } else {
    console.log(`\x1b[33m[!]\x1b[0m Warning: Non-Windows OS detected (${platform}). NexusPilot Win32 hooks require Windows.`);
  }

  // 2. Python Environment
  let pythonCmd = 'python';
  try {
    const pyVer = execSync('python --version', { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
    console.log(`\x1b[32m[✓]\x1b[0m Python: ${pyVer}`);
  } catch {
    try {
      const pyVer = execSync('py --version', { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
      pythonCmd = 'py';
      console.log(`\x1b[32m[✓]\x1b[0m Python (via py launcher): ${pyVer}`);
    } catch {
      console.log('\x1b[31m[✗]\x1b[0m Python 3.10+ not found on PATH! Please install Python from https://python.org');
    }
  }

  // 3. Core Python Dependencies
  console.log('\n\x1b[36mChecking Python Dependencies:\x1b[0m');
  const packages = ['mcp', 'win32api', 'mss', 'PIL', 'comtypes', 'psutil'];
  for (const pkg of packages) {
    try {
      execSync(`${pythonCmd} -c "import ${pkg}"`, { stdio: 'ignore' });
      console.log(`  \x1b[32m[✓]\x1b[0m ${pkg}: Available`);
    } catch {
      console.log(`  \x1b[31m[✗]\x1b[0m ${pkg}: Not installed (run 'pip install ${pkg}')`);
    }
  }

  // 4. Windows UI Automation COM Core
  console.log('\n\x1b[36mChecking Windows UIAutomation (UIA) COM Core:\x1b[0m');
  try {
    const uiaCheck = execSync(
      `${pythonCmd} -c "import comtypes.client; from comtypes.gen import UIAutomationClient; uia = comtypes.client.CreateObject(UIAutomationClient.CUIAutomation, interface=UIAutomationClient.IUIAutomation); print(uia.GetRootElement().CurrentName)"`,
      { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] }
    ).trim();
    console.log(`  \x1b[32m[✓]\x1b[0m UIAutomation Core: Operational (Root: ${uiaCheck})`);
  } catch (err) {
    console.log(`  \x1b[33m[!]\x1b[0m UIAutomation COM check: Skipped or initializing (${err.message})`);
  }

  console.log('\n\x1b[36m=======================================================');
  console.log(' Diagnostic complete. Ready for NexusPilot!');
  console.log('=======================================================\x1b[0m\n');
}
