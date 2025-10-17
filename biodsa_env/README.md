# BioDSA Sandbox Environments

This directory contains Docker-based sandbox environments for secure code execution in BioDSA agents.

## 📂 Directory Structure

```
biodsa_env/
├── python_sandbox/          # Python 3.12 execution environment
│   ├── Dockerfile          # Docker image definition
│   ├── Pipfile            # Python package dependencies
│   ├── build_sandbox.sh   # Build script
│   └── build.log          # Build output log (generated)
├── r_sandbox/             # R execution environment (coming soon)
│   └── README.md
└── README.md              # This file
```

## 🐍 Python Sandbox

The Python sandbox provides an isolated environment with pre-installed data science packages for biomedical analysis.

### Prerequisites

- Docker Desktop or Docker Engine installed
- Docker daemon running (verify with `docker ps`)

---

## 🚀 Install the Sandbox Image

### Step 1: Navigate to the Python sandbox directory

```bash
cd python_sandbox
```

### Step 2: Run the build script

```bash
./build_sandbox.sh
```

If you get a permission error, make the script executable first:

```bash
chmod +x build_sandbox.sh
./build_sandbox.sh
```

### Step 3: Monitor build progress

The build runs in the background. Monitor progress with:

```bash
tail -f build.log
```

Build time: **5-10 minutes** (depending on network speed and system resources)

### Step 4: Verify installation

Check that the image was created successfully:

```bash
docker images | grep biodsa-sandbox-py
```

Expected output:
```
biodsa-sandbox-py    latest    abc123def456    2 minutes ago    1.2GB
```

### Test the sandbox

Run a quick test to verify Python and packages work:

```bash
docker run --rm biodsa-sandbox-py:latest python -c "import pandas, matplotlib, seaborn; print('✓ Sandbox working!')"
```

---

## 🔧 Customize the Sandbox

You can add or modify Python packages to suit your analysis needs.

### Step 1: Edit the Pipfile

Open `python_sandbox/Pipfile` in your editor:

```bash
cd python_sandbox
nano Pipfile  # or vim, code, etc.
```

### Step 2: Add your packages

Add new packages under the `[packages]` section:

```toml
[packages]
# Existing packages
pytest = "*"
pandas = "*"
matplotlib = "*"
# ... other packages ...

# Add your custom packages below:
scipy = "*"                    # Scientific computing
networkx = "*"                 # Network analysis
biopython = "*"                # Biological computation
xgboost = "*"                  # Gradient boosting
torch = "*"                    # Deep learning
```

**Version specifications:**
- `"*"` - Install latest version (recommended)
- `"==1.2.3"` - Install specific version
- `">=1.2.0"` - Install minimum version or higher

**Python version:**
- Fixed at Python 3.12.11 (specified in `[requires]` section)
- Do not modify the Python version unless you rebuild the base Dockerfile

### Step 3: Rebuild the sandbox

After saving your changes, rebuild the Docker image:

```bash
./build_sandbox.sh
```

This will:
1. ✅ Read your updated Pipfile
2. ✅ Resolve dependencies and create Pipfile.lock
3. ✅ Install all packages in the container
4. ✅ Build a new `biodsa-sandbox-py:latest` image

### Step 4: Verify your changes

Test that your new package is available:

```bash
# Example: Test scipy installation
docker run --rm biodsa-sandbox-py:latest python -c "import scipy; print(f'scipy version: {scipy.__version__}')"

# Example: Test multiple packages
docker run --rm biodsa-sandbox-py:latest python -c "import torch, networkx; print('✓ Custom packages installed!')"
```

---

## 📦 Pre-installed Packages

The default Python sandbox includes:

### Data Processing & Analysis
- `pandas` - DataFrames and data manipulation
- `numpy` - Numerical computing (installed as pandas dependency)
- `pydantic` - Data validation

### Visualization
- `matplotlib` - Basic plotting
- `seaborn` - Statistical visualizations
- `plotly` - Interactive plots
- `kaleido` - Static image export for plotly
- `mpld3` - Interactive matplotlib figures
- `pycomplexheatmap` - Complex heatmaps
- `ridgeplot` - Ridge plots

### Statistical Analysis
- `statsmodels` - Statistical models
- `lifelines` - Survival analysis
- `scikit-learn` - Machine learning

### Utilities
- `pytest` - Testing framework
- `jupyter` - Jupyter notebook support
- `tabulate` - Pretty tables
- `trio` - Async I/O

### Development
- `pip` - Package installer

---

## 🏗️ Sandbox Architecture

### How it works

1. **Base Image**: `python:3.12-slim` (minimal Debian with Python 3.12)
2. **Package Manager**: `pipenv` for reproducible builds
3. **Installation**: Packages installed system-wide (no virtual environment)
4. **Runtime**: Container runs indefinitely with `sleep infinity`

### Dockerfile Structure

```dockerfile
FROM python:3.12-slim              # Lightweight Python base image
RUN apt-get update                 # Update system packages
RUN pip install pipenv==2023.11.17 # Install pipenv for dependency management
RUN mkdir /sandbox                 # Create working directory
COPY Pipfile /sandbox/             # Copy package specifications
WORKDIR /sandbox                   # Set working directory
ENV PIPENV_VENV_IN_PROJECT=false   # Install packages globally
RUN pipenv lock && pipenv install --system --deploy  # Lock deps and install
CMD ["sleep", "infinity"]          # Keep container running
```

### Image Details

- **Name**: `biodsa-sandbox-py:latest`
- **Tag**: `latest` (overwritten on each build)
- **Working Directory**: `/sandbox` (inside container)
- **Execution Directory**: `/workdir` (mounted at runtime by BioDSA agents)

---

## 🛠️ Troubleshooting

### Build Issues

**Problem**: `permission denied: './build_sandbox.sh'`
```bash
chmod +x python_sandbox/build_sandbox.sh
```

**Problem**: `Cannot connect to the Docker daemon`
```bash
# Check if Docker is running
docker ps

# Start Docker (macOS/Windows: open Docker Desktop)
# Linux:
sudo systemctl start docker
```

**Problem**: `Locking failed` or dependency conflicts
```bash
# Check build.log for details
cat python_sandbox/build.log

# Solutions:
# 1. Remove version constraints (use "*")
# 2. Update pipenv
pip install --upgrade pipenv

# 3. Clean Docker cache and rebuild
docker system prune -a
./build_sandbox.sh
```

**Problem**: Build runs out of disk space
```bash
# Clean up old Docker images
docker system prune -a

# Check disk space
df -h
```

### Runtime Issues

**Problem**: Package import fails in sandbox
```bash
# Verify package is in Pipfile
cat python_sandbox/Pipfile

# Rebuild if needed
cd python_sandbox && ./build_sandbox.sh
```

**Problem**: Sandbox container won't start
```bash
# Check Docker logs
docker ps -a
docker logs <container_id>

# Remove old containers
docker container prune
```

---

## 📊 R Sandbox

R sandbox support is currently under development. 

**Status**: Coming soon  
**Planned features**:
- R 4.x base environment
- Bioconductor packages
- tidyverse ecosystem
- Statistical analysis libraries

Stay tuned for updates!

---

## 💡 Tips

### Keep packages minimal
Only include packages you actually need. Smaller images:
- ✅ Build faster
- ✅ Use less disk space
- ✅ Start containers quicker

### Use version pinning for reproducibility
For production/research workflows, pin versions:
```toml
pandas = "==2.0.0"
scikit-learn = "==1.3.0"
```

### Clean up regularly
Remove unused images and containers:
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove everything (use with caution!)
docker system prune -a
```

### Test before deploying
Always test the sandbox after customization:
```bash
docker run --rm biodsa-sandbox-py:latest python -c "import your_package"
```

---

## 📚 Additional Resources

- **Docker Documentation**: https://docs.docker.com/
- **Pipenv Documentation**: https://pipenv.pypa.io/
- **Python Packaging**: https://packaging.python.org/

For issues specific to BioDSA agents, see the main repository README.
