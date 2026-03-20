# Releasing

## Goal

This project is packaged as a Python CLI so it can be shared without asking users to edit source files.

Primary entrypoint:

```bash
youtube-playlist-manager
```

## Local Build

Create build artifacts locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade build
python -m build
```

Artifacts are written to:

- `dist/*.whl`
- `dist/*.tar.gz`

## Local Install Test

In a fresh virtualenv, install the built wheel:

```bash
python3 -m venv /tmp/ypm-test-venv
source /tmp/ypm-test-venv/bin/activate
pip install dist/*.whl
youtube-playlist-manager --help
```

## Share Options

### Option 1: Share the repository

Users clone the repo and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Option 2: Share a wheel

Build once and send the wheel from `dist/`. Users install it with:

```bash
pip install youtube_playlist_manager-<version>-py3-none-any.whl
```

### Option 3: Publish to PyPI

Once the package metadata is finalized and the project name is confirmed available, publish so users can install with:

```bash
pip install youtube-playlist-manager
```

As of March 20, 2026, direct checks to these PyPI JSON endpoints returned `404`, which indicates the name appears available at that time:

- `https://pypi.org/pypi/youtube-playlist-manager/json`
- `https://pypi.org/pypi/youtube_playlist_manager/json`

## Before Publishing

- confirm package name availability
- create a PyPI account and API token
- review README for installation and security guidance
- ensure no credentials or token files are included
- verify `youtube-playlist-manager --help`
- test one real OAuth flow
- run `twine check dist/*`
- upload with `twine upload dist/*`

## First Release Commands

Build and validate:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

Upload using a PyPI API token:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-pypi-api-token>
python -m twine upload dist/*
```

If you want to test the publish flow first, use TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

## Planned Improvement

Persistent login currently uses a local token file only when `--remember-me` is enabled.

Next security improvement:

- replace file-based persistent token storage with OS-native secure storage
