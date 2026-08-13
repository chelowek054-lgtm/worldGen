from pathlib import Path

import pytest
import torch
import yaml
from PIL import Image

from worldgen.dna.dataset import (
    MultiViewPairDataset,
    SyntheticMultiViewDataset,
    load_manifest,
)


def test_synthetic_dataset_pair_shapes():
    dataset = SyntheticMultiViewDataset(n_objects=4, image_size=32, seed=0)
    item = dataset[0]
    assert item["anchor"].shape == (3, 32, 32)
    assert item["positive"].shape == (3, 32, 32)
    assert item["object_id"] == "0"


def test_synthetic_dataset_same_object_more_similar_than_different():
    dataset = SyntheticMultiViewDataset(n_objects=8, image_size=16, noise_std=0.02, seed=0)
    item_a = dataset[0]
    item_b = dataset[1]

    same_object_dist = torch.norm(item_a["anchor"] - item_a["positive"])
    diff_object_dist = torch.norm(item_a["anchor"] - item_b["anchor"])

    assert same_object_dist < diff_object_dist


def test_load_manifest_and_pair_dataset(tmp_path: Path):
    obj_dir = tmp_path / "renders" / "obj_01"
    obj_dir.mkdir(parents=True)
    view_paths = []
    for i in range(3):
        p = obj_dir / f"view_{i}.png"
        Image.new("RGB", (8, 8), color=(i * 10, 0, 0)).save(p)
        view_paths.append(f"renders/obj_01/view_{i}.png")

    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump({"objects": [{"id": "obj_01", "views": view_paths}]}),
        encoding="utf-8",
    )

    objects = load_manifest(manifest_path)
    assert len(objects) == 1
    assert objects[0].object_id == "obj_01"
    assert all(v.is_file() for v in objects[0].views)

    dataset = MultiViewPairDataset(objects, seed=0)
    assert len(dataset) == 1
    item = dataset[0]
    assert item["anchor"].shape[0] == 3


def test_multiview_dataset_rejects_objects_without_enough_views():
    from worldgen.dna.dataset import ObjectViews

    with pytest.raises(ValueError):
        MultiViewPairDataset([ObjectViews(object_id="x", views=[Path("only_one.png")])])
