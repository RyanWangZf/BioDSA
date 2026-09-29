import json
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
            verifier = text.split("BIOAGENT_ITEM_IDS:", 1)[1].split("}", 1)[0].strip().strip('"')
            for item_id in verifier.split(","):
                self.assertIn(f'"{item_id}"', text)


if __name__ == "__main__":
    unittest.main()
