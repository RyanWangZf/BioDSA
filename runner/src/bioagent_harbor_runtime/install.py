from __future__ import annotations

import importlib.metadata
import json
import shlex
import shutil
from pathlib import Path


def stage_agent(package_dir: Path, distribution: str, package_name: str, stage: Path) -> None:
    """Stage agent/runtime sources and non-Harbor declared dependencies."""
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(package_dir, stage / package_name)
    runtime = Path(__file__).resolve().parent
    shutil.copytree(runtime, stage / "bioagent_harbor_runtime")
    requirements = []
    for requirement in importlib.metadata.requires(distribution) or []:
        lowered = requirement.lower()
        if lowered.startswith("bioagent-harbor-runtime") or "extra ==" in lowered:
            continue
        requirements.append(requirement)
    (stage / "requirements.json").write_text(json.dumps(requirements))


def install_command(stage: str, environment_dir: str, package_name: str) -> str:
    """Return a fixed-shell command that creates one reusable agent environment."""
    script = (
        "import json,pathlib,shutil,site,subprocess,sys;"
        f"stage=pathlib.Path({stage!r});env=pathlib.Path({environment_dir!r});"
        "subprocess.run([sys.executable,'-m','venv',str(env)],check=True);"
        "python=env/'bin/python';pip=env/'bin/pip';"
        "requirements=json.loads((stage/'requirements.json').read_text());"
        "subprocess.run([str(pip),'install','--disable-pip-version-check',*requirements],check=True) if requirements else None;"
        "target=subprocess.check_output([str(python),'-c','import site; print(site.getsitepackages()[0])'],text=True).strip();"
        f"shutil.copytree(stage/{package_name!r},pathlib.Path(target)/{package_name!r},dirs_exist_ok=True);"
        "shutil.copytree(stage/'bioagent_harbor_runtime',pathlib.Path(target)/'bioagent_harbor_runtime',dirs_exist_ok=True)"
    )
    return "python3 -c " + shlex.quote(script)
