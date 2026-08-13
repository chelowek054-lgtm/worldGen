"""Контрастивный лосс L_identity (фаза 1.2): позитивы близко, негативы далеко.

InfoNCE / NT-Xent по батчу пар (anchor, positive) — два вида одного объекта.
Остальные элементы батча (виды других объектов) — in-batch негативы. Тот же приём,
что и в SimCLR; корректен, только пока в батче каждый объект встречается не
больше раза (см. `worldgen.dna.dataset` — по построению так и есть: один индекс
датасета = один объект).
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def info_nce_loss(
    anchor: torch.Tensor, positive: torch.Tensor, temperature: float = 0.1
) -> torch.Tensor:
    """anchor, positive: [B, d], по одному объекту в каждой строке (без повторов).

    Симметричный NT-Xent: диагональ similarity-матрицы — позитивы, остальное —
    in-batch негативы.
    """
    if anchor.shape[0] < 2:
        raise ValueError("in-batch негативы требуют batch_size >= 2")

    anchor = F.normalize(anchor, dim=-1)
    positive = F.normalize(positive, dim=-1)

    logits = anchor @ positive.T / temperature  # [B, B]
    labels = torch.arange(anchor.shape[0], device=anchor.device)

    loss_a2p = F.cross_entropy(logits, labels)
    loss_p2a = F.cross_entropy(logits.T, labels)
    return (loss_a2p + loss_p2a) / 2


def identity_margin(anchor: torch.Tensor, positive: torch.Tensor) -> torch.Tensor:
    """Диагностика ✅ шага 1.2: cos(anchor, positive) − cos(anchor, самый похожий негатив).

    Положительное и растущее значение = ДНК действительно различает объекты
    (см. «Проверка ✅» шага 1.2 в detailed-implementation-plan.md).
    """
    anchor_n = F.normalize(anchor, dim=-1)
    positive_n = F.normalize(positive, dim=-1)
    pos_sim = (anchor_n * positive_n).sum(dim=-1)  # [B]

    neg_sim = anchor_n @ positive_n.T  # [B, B]
    neg_sim.fill_diagonal_(float("-inf"))
    hardest_neg_sim = neg_sim.max(dim=-1).values

    return (pos_sim - hardest_neg_sim).mean()


__all__ = ["info_nce_loss", "identity_margin"]
