# Contributing to NexusPilot: Desktop

Thank you for your interest in contributing to **NexusPilot: Desktop**!

## Development Setup

1. **Prerequisites**:
   - Windows 10 or 11 (64-bit)
   - Python 3.10+
   - Git

2. **Clone and Install**:
   ```powershell
   git clone https://github.com/nishantshaligram/nexus-pilot-desktop.git
   cd nexus-pilot-desktop
   pip install --user -r nexus-pilot/requirements.txt
   ```

3. **Run the Diagnostic Probe**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/verify-environment.ps1
   ```

4. **Run Automated Tests**:
   ```powershell
   python nexus-pilot/tests/test_pilot.py
   ```

## Contribution Workflow

1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Write clean, modular code with descriptive docstrings and type annotations.
3. Ensure existing tests pass and add unit tests for new capabilities.
4. Commit using standard conventional commit messages (e.g. `feat:`, `fix:`, `docs:`, `test:`).
5. Open a Pull Request against `main` with a clear summary of your changes.
