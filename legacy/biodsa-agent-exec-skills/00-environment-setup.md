# 00 — Environment Setup

This guide tells you how to **automatically** set up the BioDSA development environment for the user. Do NOT ask the user to run these steps manually — run them yourself via the terminal.

> **Goal**: Get the user into an isolated Python 3.12 environment with all BioDSA dependencies installed, `.env` configured, and (optionally) the Docker sandbox built — without touching their base/system Python.

---

## Before You Start

Check what is already set up by running these checks:

```bash
# Check if we're already inside a pipenv/conda env
echo $VIRTUAL_ENV
echo $CONDA_DEFAULT_ENV

# Check if Pipfile.lock exists (dependencies already installed?)
ls Pipfile.lock

# Check if .env exists
ls .env

# Check if Docker sandbox is built
docker images | grep biodsa-sandbox-py
```

**If everything is already set up**, skip to the verification step at the bottom. Only run the steps that are missing.

---

## Step 1: Create an Isolated Python Environment

**IMPORTANT**: Never install BioDSA dependencies into the user's base/system Python. Always use an isolated environment.

### Option A: Conda + Pipenv (Recommended)

This is the safest approach — conda manages the Python version, pipenv manages the packages.

```bash
# Create a conda environment with Python 3.12
conda create -n biodsa python=3.12 -y

# Activate it
conda activate biodsa

# Install pipenv inside the conda env
pip install pipenv
```

### Option B: Pipenv Only (If conda is not available)

```bash
# Ensure Python 3.12 is available
python3.12 --version  # or python3 --version

# Install pipenv globally (if not already installed)
pip install --user pipenv
```

### How to Choose

- If `conda --version` succeeds → use **Option A**
- If conda is not installed → use **Option B**
- If neither Python 3.12 nor conda is available, tell the user to install one of them first

---

## Step 2: Install Dependencies

From the BioDSA repo root:

```bash
# If using conda, make sure the env is active
# conda activate biodsa

cd /path/to/BioDSA

# Install all dependencies from Pipfile
pipenv install

# Enter the pipenv shell (creates/activates the virtualenv)
pipenv shell
```

This installs all required packages (LangChain, LangGraph, OpenAI, Anthropic, pandas, matplotlib, etc.) in an isolated virtualenv.

**If `pipenv install` fails:**
- Check that Python 3.12 is available (`python3.12 --version`)
- Try `pipenv install --python 3.12` to explicitly specify the version
- If a specific package fails, try `pipenv install` again — transient network errors are common

---

## Step 3: Configure API Keys

```bash
cd /path/to/BioDSA

# Copy the example env file
cp .env.example .env
```

Then ask the user which LLM provider they want to use and help them fill in the `.env` file:

```bash
# At minimum, set one provider. Example for Azure OpenAI:
AZURE_OPENAI_API_KEY=<user's key>
AZURE_OPENAI_ENDPOINT=<user's endpoint>
API_TYPE=azure
MODEL_NAME=gpt-5
```

**Supported providers** (user needs at least one):

| Provider | Required Keys |
|----------|--------------|
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Google | `GOOGLE_API_KEY` |

**If the user doesn't know their keys**, tell them where to get them:
- Azure: Azure Portal → OpenAI resource → Keys and Endpoint
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys
- Google: https://aistudio.google.com/apikey

---

## Step 4: Build Docker Sandbox (Optional but Recommended)

The Docker sandbox provides secure, isolated code execution. Agents that write and run Python code (DSWizard, Coder, React) use it.

```bash
# Check if Docker is running
docker info > /dev/null 2>&1 && echo "Docker is running" || echo "Docker is NOT running"
```

**If Docker is running:**

```bash
cd /path/to/BioDSA/biodsa_env/python_sandbox
chmod +x build_sandbox.sh
./build_sandbox.sh
```

This builds in the background (5-10 minutes). Monitor with:

```bash
tail -f /path/to/BioDSA/biodsa_env/python_sandbox/build.log
```

Verify when done:

```bash
docker images | grep biodsa-sandbox-py
```

**If Docker is NOT running or not installed:**
- Tell the user that agents will fall back to local code execution (less secure but functional)
- This is fine for prototyping; recommend Docker for production use

---

## Step 5: Verify the Setup

Run these verification commands and confirm all pass:

```bash
cd /path/to/BioDSA

# 1. Check Python version
python --version  # Should be 3.12.x

# 2. Check core dependencies
python -c "
import langchain, langgraph, openai, pandas, matplotlib
print('Core dependencies: OK')
"

# 3. Check BioDSA imports
python -c "
from biodsa.agents import BaseAgent, CoderAgent, ReactAgent, DSWizardAgent
print('BioDSA agents: OK')
"

# 4. Check .env is loadable
python -c "
from dotenv import load_dotenv
import os
load_dotenv('.env')
keys = [k for k in ['OPENAI_API_KEY', 'AZURE_OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY'] if os.environ.get(k)]
print(f'API keys configured: {len(keys)} provider(s)')
assert len(keys) > 0, 'No API keys found in .env!'
print('.env: OK')
"

# 5. (Optional) Check Docker sandbox
docker run --rm biodsa-sandbox-py:latest python -c "
import pandas, matplotlib, seaborn
print('Docker sandbox: OK')
" 2>/dev/null || echo "Docker sandbox: not available (will use local execution)"
```

**If any check fails**, diagnose and fix before proceeding with the user's task.

---

## Quick Reference: Common Environment Commands

```bash
# Activate the conda env (if using conda)
conda activate biodsa

# Enter the pipenv shell
cd /path/to/BioDSA && pipenv shell

# Run a script inside the pipenv env (without entering shell)
cd /path/to/BioDSA && pipenv run python run_task.py

# Install a new dependency
pipenv install <package_name>

# Deactivate
exit  # exits pipenv shell
conda deactivate  # exits conda env
```

---

## When to Run Setup

- **First time**: Run all steps (1 through 5)
- **Returning user**: Just activate the env (`conda activate biodsa && pipenv shell`) and verify
- **After `git pull`**: Run `pipenv install` again to pick up new dependencies
- **New API provider**: Update `.env` with the new keys
