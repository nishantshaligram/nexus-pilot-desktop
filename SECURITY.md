# Security Policy

## Responsible Disclosure

The NexusPilot team takes security seriously, especially given that this software interacts directly with operating system input queues, display surfaces, and accessibility trees.

If you discover a security vulnerability or bypass of safety boundaries in NexusPilot, please report it privately:

- **Email**: nishant.shaligram@gmail.com
- Please include steps to reproduce, affected version, and your Windows environment details.
- We aim to acknowledge receipt within 48 hours and provide a remediation timeline.

Please do not open public GitHub issues for undisclosed security vulnerabilities.

## Threat Model & Safety Boundaries

NexusPilot includes built-in safeguards:
1. **Hardware Corner Failsafe**: Moving the cursor to `(0, 0)` immediately aborts automation.
2. **Application Boundary Locks**: Restricts simulated mouse actions to explicit application window handles.
3. **UIPI Isolation**: Runs in unprivileged user space by default to avoid unintended access to elevated administrator processes.
