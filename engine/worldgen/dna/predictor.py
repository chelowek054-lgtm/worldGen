"""Инференс: изображение объекта → ДНК. Загружает бэкбон и компрессор из чекпоинта.

Как и в `Predictor` из pet-проекта OCR (`docs/developers/ocr-pipeline-lessons.md`),
конфигурация бэкбона/компрессора берётся из самого чекпоинта, а не из текущего
Hydra-конфига — инференс воспроизводим независимо от того, что лежит в
`configs/dna/config.yaml` на момент запуска.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image

from worldgen.dna.backbone import FeatureBackbone, build_backbone
from worldgen.dna.checkpoints import load_checkpoint
from worldgen.dna.dataset import default_transform
from worldgen.dna.model import DNACompressor


class DNAPredictor:
    """Инференс-пайплайн ДНК-компрессора."""

    def __init__(
        self,
        checkpoint_path: str | Path,
        backbone: FeatureBackbone | None = None,
        device: str | torch.device = "cpu",
    ) -> None:
        self.device = torch.device(device)
        checkpoint = load_checkpoint(checkpoint_path, map_location=self.device)
        cfg = checkpoint.config

        self.backbone = backbone or build_backbone(cfg.get("backbone", {"name": "random"}))
        self.compressor = DNACompressor(
            feature_dim=self.backbone.feature_dim,
            dna_dim=int(cfg.get("dna_dim", 256)),
            n_tokens=int(cfg.get("n_tokens", 8)),
            n_layers=int(cfg.get("n_layers", 2)),
            n_heads=int(cfg.get("n_heads", 8)),
        )
        self.compressor.load_state_dict(checkpoint.model_state_dict)
        self.compressor.to(self.device).eval()

    @torch.no_grad()
    def encode(self, image: str | Path | Image.Image) -> np.ndarray:
        """Изображение (crop объекта) → ДНК, массив формы `[n_tokens, dna_dim]`."""
        if isinstance(image, (str, Path)):
            image = Image.open(image)
        tensor = default_transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        patch_features = self.backbone(tensor)
        dna = self.compressor(patch_features)
        return dna.squeeze(0).cpu().numpy()


__all__ = ["DNAPredictor"]
