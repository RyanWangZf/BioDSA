import json
import tempfile
import unittest
from pathlib import Path

from bioagent_harbor_runtime.batch import _load_items

class BatchRuntimeTests(unittest.TestCase):
    def test_per_dataset_selection_is_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory); (app / "data").mkdir()
            (app / "data/items.jsonl").write_text(json.dumps({"item_id":"known", "source_split":"fit"}) + "\n")
            (app / "data/manifest.json").write_text(json.dumps({"subset":"fixture"}))
            with self.assertRaisesRegex(ValueError, "unknown item_ids"):
                _load_items({"instruction":"x", "split":"fit", "item_ids_by_dataset":{"fixture":["missing"]}}, app, False, {"fit"})
            with self.assertRaisesRegex(ValueError, "no selection"):
                _load_items({"instruction":"x", "split":"fit", "item_ids_by_dataset":{"other":["known"]}}, app, False, {"fit"})

if __name__ == "__main__": unittest.main()
