"""Тесты оценочного инструментария 0.1: perceptual hash, overlap, manifest."""

from __future__ import annotations

import numpy as np
from PIL import Image

from worldgen.eval.manifest import GoldenSetManifest
from worldgen.eval.overlap import find_collisions
from worldgen.eval.phash import dhash, hamming


def _img(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(arr.astype(np.uint8))


def _gradient(seed: int, size: int = 64) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = np.linspace(0, 255, size, dtype=np.float64)
    grid = np.tile(base, (size, 1)) + rng.integers(0, 8, (size, size))
    return np.clip(grid, 0, 255)


# --- perceptual hash ---

def test_dhash_identical_is_zero_distance() -> None:
    img = _img(_gradient(1))
    assert hamming(dhash(img), dhash(img.copy())) == 0


def test_dhash_robust_to_resize_and_jpeg_like() -> None:
    img = _img(_gradient(2))
    smaller = img.resize((32, 32)).resize((64, 64))
    assert hamming(dhash(img), dhash(smaller)) <= 5


def test_dhash_distinguishes_different_images() -> None:
    a = _img(_gradient(3))
    b = _img(np.rot90(_gradient(3)))
    assert hamming(dhash(a), dhash(b)) > 5


# --- overlap ---

def test_overlap_flags_duplicate(tmp_path) -> None:
    eval_dir = tmp_path / "eval"
    train_dir = tmp_path / "train"
    eval_dir.mkdir()
    train_dir.mkdir()

    shared = _img(_gradient(10))
    shared.save(eval_dir / "obj.png")
    shared.resize((48, 48)).resize((64, 64)).save(train_dir / "leaked.png")  # near-dup
    _img(np.rot90(_gradient(99))).save(eval_dir / "unique.png")

    collisions = find_collisions(eval_dir, [train_dir], threshold=5)
    assert len(collisions) == 1
    assert collisions[0].eval_path.name == "obj.png"


def test_overlap_clean_when_disjoint(tmp_path) -> None:
    eval_dir = tmp_path / "eval"
    train_dir = tmp_path / "train"
    eval_dir.mkdir()
    train_dir.mkdir()
    _img(_gradient(1)).save(eval_dir / "a.png")
    _img(np.rot90(_gradient(1))).save(train_dir / "b.png")

    assert find_collisions(eval_dir, [train_dir], threshold=5) == []


# --- manifest ---

def _write_manifest(tmp_path, body: str):
    (tmp_path / "manifest.yaml").write_text(body, encoding="utf-8")
    return tmp_path / "manifest.yaml"


def test_manifest_counts_and_missing(tmp_path) -> None:
    (tmp_path / "objects" / "mug").mkdir(parents=True)
    _img(_gradient(5)).save(tmp_path / "objects" / "mug" / "v0.png")
    path = _write_manifest(
        tmp_path,
        "version: 0\n"
        "objects:\n"
        "  - id: mug\n"
        "    category: rigid\n"
        "    views: [objects/mug/v0.png, objects/mug/v1.png]\n",
    )
    m = GoldenSetManifest.load(path)
    assert m.counts()["objects"] == 1
    assert m.counts()["files"] == 2
    assert m.missing_files() == ["objects/mug/v1.png"]


def test_manifest_set_hash_deterministic_and_content_sensitive(tmp_path) -> None:
    (tmp_path / "objects" / "mug").mkdir(parents=True)
    view = tmp_path / "objects" / "mug" / "v0.png"
    _img(_gradient(5)).save(view)
    path = _write_manifest(
        tmp_path,
        "version: 0\nobjects:\n  - id: mug\n    views: [objects/mug/v0.png]\n",
    )
    m = GoldenSetManifest.load(path)
    h1 = m.set_hash()
    assert h1 == GoldenSetManifest.load(path).set_hash()  # детерминизм

    _img(_gradient(6)).save(view)  # меняем содержимое файла
    assert GoldenSetManifest.load(path).set_hash() != h1  # хеш реагирует
