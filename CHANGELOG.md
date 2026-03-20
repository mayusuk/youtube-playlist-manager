# Changelog

## 0.1.0 - 2026-03-20

Initial shareable release.

- packaged the project as an installable Python CLI
- replaced hardcoded playlist and credential paths with CLI inputs
- added support for WhatsApp `.txt` and `.zip` exports
- added playlist lookup by title, ID, or URL with create-if-missing behavior
- added duplicate detection based on actual playlist contents
- switched to session-only OAuth by default, with optional `--remember-me`
- added optional non-YouTube link fallback using YouTube search
- added tests for chat parsing and search-candidate extraction
- added release documentation and buildable wheel/sdist artifacts
