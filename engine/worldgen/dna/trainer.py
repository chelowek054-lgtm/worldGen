"""Цикл обучения ДНК-компрессора (задача 1.2): контрастив на позитивных/негативных парах.

Бэкбон всегда заморожен — обучается только `DNACompressor`. Лучший по
`identity_margin` (см. `losses.py`) чекпоинт сохраняется через
`checkpoints.save_checkpoint`. Планка обучения (`AdamW` + `weight_decay`) — по
опыту pet-проекта OCR, см. `docs/developers/ocr-pipeline-lessons.md`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader

from worldgen.dna.backbone import FeatureBackbone
from worldgen.dna.checkpoints import Checkpoint, save_checkpoint
from worldgen.dna.losses import identity_margin, info_nce_loss
from worldgen.dna.model import DNACompressor, pooled_embedding
from worldgen.tracking.base import Tracker


class DNATrainer:
    def __init__(
        self,
        backbone: FeatureBackbone,
        compressor: DNACompressor,
        tracker: Tracker,
        lr: float = 1e-4,
        weight_decay: float = 1e-4,
        device: str | torch.device = "cpu",
    ) -> None:
        self.backbone = backbone
        self.compressor = compressor.to(device)
        self.tracker = tracker
        self.device = torch.device(device)
        self.optimizer = torch.optim.AdamW(
            self.compressor.parameters(), lr=lr, weight_decay=weight_decay
        )
        self.best_margin = float("-inf")

    def _encode(self, images: torch.Tensor) -> torch.Tensor:
        images = images.to(self.device)
        patch_features = self.backbone(images)
        dna = self.compressor(patch_features)
        return pooled_embedding(dna)

    def train_epoch(self, loader: DataLoader) -> dict[str, float]:
        self.compressor.train()
        total_loss, total_margin, n_batches = 0.0, 0.0, 0

        for batch in loader:
            anchor_emb = self._encode(batch["anchor"])
            positive_emb = self._encode(batch["positive"])

            loss = info_nce_loss(anchor_emb, positive_emb)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            with torch.no_grad():
                margin = identity_margin(anchor_emb, positive_emb)

            total_loss += float(loss.item())
            total_margin += float(margin.item())
            n_batches += 1

        return {
            "loss": total_loss / max(n_batches, 1),
            "identity_margin": total_margin / max(n_batches, 1),
        }

    def fit(
        self,
        loader: DataLoader,
        epochs: int,
        run_name: str,
        checkpoint_path: str | Path,
        config_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, float]:
        self.tracker.start_run(run_name, params=config_snapshot or {})
        metrics: dict[str, float] = {}

        for epoch in range(epochs):
            metrics = self.train_epoch(loader)
            self.tracker.log_metrics(metrics, step=epoch)

            if metrics["identity_margin"] > self.best_margin:
                self.best_margin = metrics["identity_margin"]
                save_checkpoint(
                    checkpoint_path,
                    Checkpoint(
                        model_state_dict=self.compressor.state_dict(),
                        config=config_snapshot or {},
                        epoch=epoch,
                        metric=self.best_margin,
                    ),
                )

        self.tracker.end_run()
        return metrics


__all__ = ["DNATrainer"]
