"""Fetch the pinned BioDSBench Python archive and stage inputs for four tasks."""
from __future__ import annotations

import csv
import io
import ssl
import tarfile
import urllib.request
from pathlib import Path

REVISION = "e59af82ee9461db78ed399544ec8520afeb02ce5"
URL = f"https://huggingface.co/datasets/zifeng-ai/BioDSBench/resolve/{REVISION}/data_files/raw_patient_data_for_python_tasks.tar.gz"
TASKS = ("27959731_0", "27959731_2", "27959731_3", "27959731_4")
FILES = ("data_clinical_patient", "data_clinical_sample", "data_mutations")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cache = Path.home() / ".cache" / "bioagent-gym" / "harbor" / "BioDSBench" / REVISION
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / "raw_patient_data_for_python_tasks.tar.gz"
    if not archive.exists() or not tarfile.is_tarfile(archive):
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            context = ssl.create_default_context()
        with urllib.request.urlopen(URL, context=context) as response, archive.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
    with tarfile.open(archive, "r:gz") as bundle:
        for stem in FILES:
            member = bundle.getmember(f"datasets/27959731/data/{stem}.txt")
            source = io.TextIOWrapper(bundle.extractfile(member), encoding="utf-8", newline="")
            rows = list(csv.reader(source, delimiter="\t"))
            for task_id in TASKS:
                for phase in ("environment", "tests"):
                    target = root / "benchmarks" / "biodsbench" / "tasks" / task_id / phase / "inputs" / f"{stem}.csv"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("w", newline="") as handle:
                        csv.writer(handle).writerows(rows)
    print(f"Prepared BioDSBench revision {REVISION} for {len(TASKS)} Harbor tasks")


if __name__ == "__main__":
    main()
