import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bioagent_harbor_runtime.install import install_command, stage_agent


class AgentInstallTests(unittest.TestCase):
    def test_stage_uses_declared_non_harbor_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); package=root/"source"; package.mkdir(); (package/"__init__.py").write_text("")
            with patch("importlib.metadata.requires", return_value=["bioagent-harbor-runtime==0.1.0", 'harbor==0.23.0; extra == "harbor"', "example-sdk==1.2.3"]):
                stage_agent(package,"fixture","fixture_agent",root/"stage")
            self.assertEqual(json.loads((root/"stage/requirements.json").read_text()),["example-sdk==1.2.3"])

    def test_install_command_creates_reusable_isolated_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); stage=root/"stage with spaces"; stage.mkdir()
            (stage/"fixture_agent").mkdir(); (stage/"fixture_agent/__init__.py").write_text("VALUE=7\n")
            runtime=Path(__file__).resolve().parents[1]/"src/bioagent_harbor_runtime"
            import shutil
            shutil.copytree(runtime,stage/"bioagent_harbor_runtime")
            (stage/"requirements.json").write_text("[]")
            env=root/"agent env"
            subprocess.run(install_command(str(stage),str(env),"fixture_agent"),shell=True,check=True)
            output=subprocess.check_output([str(env/"bin/python"),"-c","import fixture_agent,bioagent_harbor_runtime;print(fixture_agent.VALUE)"],text=True)
            self.assertEqual(output.strip(),"7")


if __name__ == "__main__": unittest.main()
