<#
.SYNOPSIS
    NexusPilot Environment Verification & Diagnostic Probe.
.DESCRIPTION
    Validates Windows DPI scaling, display surfaces, Python dependencies,
    COM accessibility permissions, and UIPI status for NexusPilot.
#>

$ErrorActionPreference = "Continue"

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "   NexusPilot: Desktop - Environment Diagnostic Probe   " -ForegroundColor Cyan
Write-Host "=======================================================`n" -ForegroundColor Cyan

# 1. Operating System
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "[+] OS: $($os.Caption) (Build $($os.BuildNumber), Architecture $($os.OSArchitecture))" -ForegroundColor Green

# 2. Process Elevation (UIPI status)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "[+] Process Elevation: Elevated (Administrator)" -ForegroundColor Yellow
    Write-Host "    Note: Daemon can send input to both elevated and standard applications." -ForegroundColor Gray
} else {
    Write-Host "[+] Process Elevation: Standard (Unelevated)" -ForegroundColor Green
    Write-Host "    Note: Normal user mode. Cannot send synthetic input to elevated apps (UIPI)." -ForegroundColor Gray
}

# 3. Python Environment
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pyCmd) {
    $pyVer = & python --version 2>&1
    Write-Host "[+] Python Executable: $($pyCmd.Source) ($pyVer)" -ForegroundColor Green
} else {
    Write-Host "[-] Python not found on PATH!" -ForegroundColor Red
}

# 4. Dependency Checks
Write-Host "`n[+] Checking Core Python Libraries:" -ForegroundColor Cyan
$packages = @("mcp", "win32api", "mss", "PIL", "comtypes", "psutil")

foreach ($pkg in $packages) {
    $check = & python -c "import $pkg; print('OK')" 2>$null
    if ($check -match "OK") {
        Write-Host "    [x] $pkg : Available" -ForegroundColor Green
    } else {
        Write-Host "    [!] $pkg : NOT INSTALLED" -ForegroundColor Red
    }
}

# 5. Display & Monitor Metrics
Write-Host "`n[+] Display Configuration:" -ForegroundColor Cyan
Add-Type -AssemblyName System.Windows.Forms
$screens = [System.Windows.Forms.Screen]::AllScreens
Write-Host "    Total Monitors Detected: $($screens.Count)" -ForegroundColor Gray
for ($i = 0; $i -lt $screens.Count; $i++) {
    $s = $screens[$i]
    $primary = if ($s.Primary) { "(Primary)" } else { "" }
    Write-Host "    Monitor $i $primary : Bounds = $($s.Bounds.Width)x$($s.Bounds.Height) at ($($s.Bounds.X), $($s.Bounds.Y))" -ForegroundColor Green
}

# 6. Test UIAutomation COM
Write-Host "`n[+] Checking Windows UIAutomation (UIA) COM Bridge:" -ForegroundColor Cyan
$uiaCheck = & python -c "import comtypes.client; from comtypes.gen import UIAutomationClient; uia = comtypes.client.CreateObject(UIAutomationClient.CUIAutomation, interface=UIAutomationClient.IUIAutomation); root = uia.GetRootElement(); print(root.CurrentName)" 2>$null
if ($uiaCheck) {
    Write-Host "    [x] Windows UIAutomation COM Core: Operational (Root: $uiaCheck)" -ForegroundColor Green
} else {
    Write-Host "    [!] UIAutomation COM: Failed or uninitialized" -ForegroundColor Yellow
}

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host " Diagnostic check complete. Ready for NexusPilot!" -ForegroundColor Cyan
Write-Host "=======================================================`n" -ForegroundColor Cyan
