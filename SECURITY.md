# Security policy

## Supported versions

Hearth is a local desktop-oriented app. Use the latest `main` branch when possible.

## What we care about

- Local data isolation (your SQLite path)
- No silent phone-home / telemetry in the default build
- Safe handling of untrusted character cards or imported JSON

## Reporting a vulnerability

Please open a **private** security advisory on GitHub if available, or an issue without exploit details if that is the only channel.

Include:

- Hearth version / commit
- OS
- Steps to reproduce
- Impact (data leak, RCE, etc.)

## Notes for users

- Treat character cards and UI packs from the internet like any untrusted file
- Bind Ollama and Hearth to localhost unless you intentionally expose them on a network
- Content filters are optional user settings, not a guarantee
