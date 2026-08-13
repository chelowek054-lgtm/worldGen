"""ДНК-компрессор (фаза 1.2 плана): view-invariant идентичность объекта.

Каркас заведён опережающе — до реальных мультивид-данных (задача 1.1) и до
прохождения гейта фазы 0. См. `docs/base-plans/decision-log.md`.
"""

from worldgen.dna.backbone import Dinov3Backbone, FeatureBackbone, RandomBackbone, build_backbone
from worldgen.dna.checkpoints import Checkpoint, load_checkpoint, save_checkpoint
from worldgen.dna.dataset import MultiViewPairDataset, SyntheticMultiViewDataset, load_manifest
from worldgen.dna.losses import identity_margin, info_nce_loss
from worldgen.dna.model import DNACompressor, pooled_embedding
from worldgen.dna.predictor import DNAPredictor
from worldgen.dna.trainer import DNATrainer

__all__ = [
    "FeatureBackbone",
    "RandomBackbone",
    "Dinov3Backbone",
    "build_backbone",
    "DNACompressor",
    "pooled_embedding",
    "info_nce_loss",
    "identity_margin",
    "MultiViewPairDataset",
    "SyntheticMultiViewDataset",
    "load_manifest",
    "Checkpoint",
    "save_checkpoint",
    "load_checkpoint",
    "DNATrainer",
    "DNAPredictor",
]
