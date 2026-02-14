# Manual Space + PyPI Runbook

This runbook is fully manual (no GitHub Actions).

## Scope

- Deploy `space/` to a Hugging Face Space manually.
- Publish `alteruphono` manually to TestPyPI, then PyPI.
- Switch Space dependency from GitHub pin to PyPI package after release.

## 1) One-time prerequisites

1. Install tooling locally:

```bash
uv pip install --upgrade build twine huggingface_hub
```

2. Authenticate:

```bash
huggingface-cli login
```

3. Create a Hugging Face Space (`Gradio` SDK), preferably private at first.

4. Create API tokens:
- TestPyPI token (account settings on test.pypi.org)
- PyPI token (account settings on pypi.org)

Export them in your shell:

```bash
export TWINE_USERNAME="__token__"
export TESTPYPI_TOKEN="pypi-..."
export PYPI_TOKEN="pypi-..."
```

## 2) Deploy Space manually (pre-PyPI)

The Space app lives in `space/`.

1. Keep this pre-release dependency line in `space/requirements.txt`:

`alteruphono @ git+https://github.com/tresoldi/alteruphono.git@8db0679`

2. Upload folder to your Space:

```bash
python - <<'PY'
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="space",
    repo_id="YOUR_HF_USERNAME/YOUR_SPACE_NAME",
    repo_type="space",
    commit_message="Manual deploy from local repo",
)
print("Space uploaded.")
PY
```

3. Open Space UI and verify:
- Forward: `p > b / V _ V` with `# a p a #` -> `# a b a #`
- Backward: `p > b` with `# a b a #` -> includes `# a p a #`
- Validate: `p > b / V _ V` is valid

## 3) Publish to TestPyPI (manual)

1. Ensure clean branch and run tests:

```bash
python -m pytest -q
```

2. Build distributions:

```bash
rm -rf dist/
python -m build
```

3. Check artifacts:

```bash
python -m twine check dist/*
```

4. Upload to TestPyPI:

```bash
TWINE_PASSWORD="$TESTPYPI_TOKEN" python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

5. Smoke test install from TestPyPI:

```bash
python -m venv /tmp/alteruphono-testpypi
source /tmp/alteruphono-testpypi/bin/activate
pip install --upgrade pip
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple alteruphono==1.0.0rc1
python -c "import alteruphono; print(alteruphono.__version__)"
deactivate
```

## 4) Publish to PyPI (manual)

1. Upload the same `dist/*` artifacts:

```bash
TWINE_PASSWORD="$PYPI_TOKEN" python -m twine upload dist/*
```

2. Verify install from PyPI:

```bash
python -m venv /tmp/alteruphono-pypi
source /tmp/alteruphono-pypi/bin/activate
pip install --upgrade pip
pip install alteruphono==1.0.0rc1
python -c "import alteruphono; print(alteruphono.__version__)"
deactivate
```

## 5) Post-publish Space update

1. Edit `space/requirements.txt`:

From:

`alteruphono @ git+https://github.com/tresoldi/alteruphono.git@8db0679`

To:

`alteruphono==1.0.0rc1`

2. Re-upload `space/` with the same `HfApi.upload_folder()` snippet.

3. Re-test the Space and then make it public.
