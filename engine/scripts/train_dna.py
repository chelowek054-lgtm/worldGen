"""Обучение ДНК-компрессора (задача 1.2).

Без манифеста (`data.manifest=null`, по умолчанию) обучается на синтетическом
датасете — проверяет исправность пайплайна форм/лоссов/чекпоинтов до появления
реальных мультивид-данных (задача 1.1). С манифестом — реальное обучение.

Запуск (из engine/):
    python scripts/train_dna.py
    python scripts/train_dna.py data.manifest=data/dna_train/manifest.yaml backbone=dinov3
    python scripts/train_dna.py train.epochs=1 tracking=noop
"""

from __future__ import annotations

import hydra
from omegaconf import DictConfig, OmegaConf
from torch.utils.data import DataLoader, Dataset

from worldgen.dna.backbone import build_backbone
from worldgen.dna.dataset import MultiViewPairDataset, SyntheticMultiViewDataset, load_manifest
from worldgen.dna.model import DNACompressor
from worldgen.dna.trainer import DNATrainer
from worldgen.seed import set_seed
from worldgen.tracking import build_tracker


def build_dataset(cfg: DictConfig) -> Dataset:
    if cfg.data.manifest:
        objects = load_manifest(cfg.data.manifest)
        return MultiViewPairDataset(objects, seed=int(cfg.seed))
    return SyntheticMultiViewDataset(seed=int(cfg.seed))


@hydra.main(version_base=None, config_path="../configs", config_name="dna_config")
def main(cfg: DictConfig) -> None:
    set_seed(int(cfg.seed))

    dataset = build_dataset(cfg)
    loader = DataLoader(
        dataset, batch_size=int(cfg.data.batch_size), shuffle=True, drop_last=True
    )

    backbone_cfg = OmegaConf.to_container(cfg.backbone, resolve=True)
    assert isinstance(backbone_cfg, dict)
    backbone = build_backbone(backbone_cfg)

    compressor = DNACompressor(
        feature_dim=backbone.feature_dim,
        dna_dim=int(cfg.model.dna_dim),
        n_tokens=int(cfg.model.n_tokens),
        n_layers=int(cfg.model.n_layers),
        n_heads=int(cfg.model.n_heads),
    )

    tracking_cfg = OmegaConf.to_container(cfg.tracking, resolve=True)
    assert isinstance(tracking_cfg, dict)
    tracker = build_tracker(tracking_cfg)

    trainer = DNATrainer(
        backbone,
        compressor,
        tracker,
        lr=float(cfg.train.lr),
        weight_decay=float(cfg.train.weight_decay),
    )

    metrics = trainer.fit(
        loader,
        epochs=int(cfg.train.epochs),
        run_name=str(cfg.run_name),
        checkpoint_path=cfg.checkpoint.path,
        config_snapshot={
            "backbone": backbone_cfg,
            "dna_dim": cfg.model.dna_dim,
            "n_tokens": cfg.model.n_tokens,
            "n_layers": cfg.model.n_layers,
            "n_heads": cfg.model.n_heads,
        },
    )

    print(f"[train_dna] run={cfg.run_name} metrics={metrics}")


if __name__ == "__main__":
    main()
