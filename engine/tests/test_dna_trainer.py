from pathlib import Path

from torch.utils.data import DataLoader

from worldgen.dna.backbone import RandomBackbone
from worldgen.dna.dataset import SyntheticMultiViewDataset
from worldgen.dna.model import DNACompressor
from worldgen.dna.predictor import DNAPredictor
from worldgen.dna.trainer import DNATrainer
from worldgen.seed import set_seed
from worldgen.tracking.noop_tracker import NoopTracker


def _build_trainer(device: str = "cpu") -> DNATrainer:
    backbone = RandomBackbone(feature_dim=32, seed=0)
    compressor = DNACompressor(
        feature_dim=backbone.feature_dim, dna_dim=16, n_tokens=4, n_layers=1, n_heads=4
    )
    return DNATrainer(backbone, compressor, NoopTracker(), lr=1e-3, device=device)


def test_train_epoch_runs_and_produces_metrics():
    set_seed(0)
    trainer = _build_trainer()
    dataset = SyntheticMultiViewDataset(n_objects=8, image_size=32, seed=0)
    loader = DataLoader(dataset, batch_size=4, shuffle=True, drop_last=True)

    metrics = trainer.train_epoch(loader)

    assert "loss" in metrics and "identity_margin" in metrics
    assert metrics["loss"] > 0


def test_identity_margin_improves_with_training():
    set_seed(0)
    trainer = _build_trainer()
    dataset = SyntheticMultiViewDataset(n_objects=8, image_size=32, noise_std=0.02, seed=0)
    loader = DataLoader(dataset, batch_size=4, shuffle=True, drop_last=True)

    first = trainer.train_epoch(loader)
    for _ in range(5):
        last = trainer.train_epoch(loader)

    assert last["identity_margin"] >= first["identity_margin"]


def test_fit_saves_checkpoint_and_predictor_loads_it(tmp_path: Path):
    set_seed(0)
    trainer = _build_trainer()
    dataset = SyntheticMultiViewDataset(n_objects=8, image_size=32, seed=0)
    loader = DataLoader(dataset, batch_size=4, shuffle=True, drop_last=True)

    checkpoint_path = tmp_path / "best_model.pt"
    trainer.fit(
        loader,
        epochs=2,
        run_name="test_run",
        checkpoint_path=checkpoint_path,
        config_snapshot={
            "backbone": {"name": "random", "feature_dim": 32, "seed": 0},
            "dna_dim": 16,
            "n_tokens": 4,
            "n_layers": 1,
            "n_heads": 4,
        },
    )
    assert checkpoint_path.is_file()

    predictor = DNAPredictor(checkpoint_path, backbone=RandomBackbone(feature_dim=32, seed=0))
    dna = predictor.encode(_dummy_image())
    assert dna.shape == (4, 16)


def _dummy_image():
    from PIL import Image

    return Image.new("RGB", (48, 48), color=(120, 80, 40))
