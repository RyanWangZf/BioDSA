import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DatasetTaskInventoryTests(unittest.TestCase):
    def _items(self, root):
        found = {}
        for path in sorted(root.glob("*/data/items.jsonl")):
            rows = [json.loads(line) for line in path.read_text().splitlines() if line]
            self.assertEqual(len(rows), len({row["item_id"] for row in rows}), path)
            for row in rows:
                self.assertNotIn("label", row, path)
                self.assertNotIn("reference_answer", row, path)
            found[path.parent.parent.name] = rows
        return found

    def test_complete_source_inventory(self):
        bio = self._items(ROOT / "benchmarks/biodsbench/tasks")
        self.assertEqual({name: len(rows) for name, rows in bio.items()}, {"biodsbench-python": 118, "biodsbench-r": 165})
        deep = self._items(ROOT / "benchmarks/biomedicine-deep-research/tasks")
        self.assertEqual(len(deep), 13)
        self.assertEqual(sum(map(len, deep.values())), 648)
        self.assertEqual(len({row["item_id"] for rows in deep.values() for row in rows}), 648)

    def test_full_jobs_reference_every_dataset_task(self):
        def paths(name):
            return {Path(line.split(":", 1)[1].strip()).name for line in (ROOT / "experiments" / name).read_text().splitlines() if line.strip().startswith("- path:")}
        bio_paths = paths("dswizard-full.yaml")
        deep_paths = paths("deepevidence-full.yaml")
        self.assertEqual(bio_paths, {"biodsbench-python", "biodsbench-r"})
        self.assertEqual(deep_paths, {p.name for p in (ROOT / "benchmarks/biomedicine-deep-research/tasks").iterdir() if p.is_dir()})

    def test_smoke_selection_is_shared_with_verifier(self):
        for name in ("dswizard-smoke.yaml", "deepevidence-smoke.yaml"):
            text = (ROOT / "experiments" / name).read_text()
            match = re.search(r'BIOAGENT_ITEM_IDS:\s*"([^"]+)"', text)
            self.assertIsNotNone(match)
            verifier = match.group(1)
            for item_id in verifier.split(","):
                self.assertIn(f'"{item_id}"', text)

    def test_deep_research_split_inventory_is_disjoint(self):
        deep = self._items(ROOT / "benchmarks/biomedicine-deep-research/tasks")
        by_split = {name: set() for name in ("fit", "tune", "verifier")}
        by_type = {}
        for rows in deep.values():
            for row in rows:
                by_split[row["source_split"]].add(row["item_id"])
                by_type[row["task_type"]] = by_type.get(row["task_type"], 0) + 1
        self.assertEqual({key: len(value) for key, value in by_split.items()}, {"fit": 388, "tune": 129, "verifier": 131})
        self.assertFalse(by_split["fit"] & by_split["tune"])
        self.assertFalse(by_split["fit"] & by_split["verifier"])
        self.assertFalse(by_split["tune"] & by_split["verifier"])
        self.assertEqual(by_type, {"single_choice": 367, "multi_select": 261, "evidence_gap_retrieval": 20})

    def test_split_jobs_propagate_trusted_selection(self):
        for split in ("fit", "tune", "verifier"):
            text = (ROOT / "experiments" / f"deepevidence-{split}.yaml").read_text()
            self.assertIn(f'BIOAGENT_SPLIT: "{split}"', text)
            self.assertIn(f"split: {split}", text)

    def test_biodsbench_python_mapping_covers_every_item(self):
        manifest = json.loads((ROOT / "benchmarks/biodsbench/tasks/biodsbench-python/data/manifest.json").read_text())
        stats = manifest["splits"]["benchmark"]
        self.assertEqual(stats["source_count"], 118)
        self.assertEqual(stats["scorable_count"], 118)
        self.assertEqual(stats["oracle_verified"], 112)
        self.assertEqual(len(manifest["oracle_failures"]), 6)


if __name__ == "__main__":
    unittest.main()
