"""ДНК-компрессор: сжимает патч-признаки бэкбона в N инвариантных токенов.

Perceiver-ресемплер (план допускает и Slot Attention — тот же контракт
входа/выхода): фиксированный набор обучаемых query-токенов делает кросс-внимание
к патч-признакам объекта. Единственное обучаемое звено фазы 1.2 — бэкбон
(`worldgen.dna.backbone.FeatureBackbone`) всегда заморожен.

Инъекция ДНК в генератор (IP-Adapter-стиль K/V/out) — задача 1.3, здесь не
реализована.
"""

from __future__ import annotations

import torch
from torch import nn


class _PerceiverLayer(nn.Module):
    """Один слой ресемплера: кросс-внимание query→patch + FFN, обе с residual+norm."""

    def __init__(self, dna_dim: int, n_heads: int) -> None:
        super().__init__()
        self.cross_attn = nn.MultiheadAttention(dna_dim, n_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(dna_dim)
        self.ffn = nn.Sequential(
            nn.Linear(dna_dim, dna_dim * 4),
            nn.GELU(),
            nn.Linear(dna_dim * 4, dna_dim),
        )
        self.norm2 = nn.LayerNorm(dna_dim)

    def forward(self, dna: torch.Tensor, kv: torch.Tensor) -> torch.Tensor:
        attended, _ = self.cross_attn(dna, kv, kv, need_weights=False)
        dna = self.norm1(dna + attended)
        return self.norm2(dna + self.ffn(dna))


class DNACompressor(nn.Module):
    """Perceiver-ресемплер: [B, P, feature_dim] патчей → [B, n_tokens, dna_dim] ДНК."""

    def __init__(
        self,
        feature_dim: int,
        dna_dim: int = 256,
        n_tokens: int = 8,
        n_layers: int = 2,
        n_heads: int = 8,
    ) -> None:
        super().__init__()
        if not 4 <= n_tokens <= 16:
            raise ValueError(f"n_tokens={n_tokens} вне диапазона плана [4, 16]")

        self.n_tokens = n_tokens
        self.dna_dim = dna_dim
        self.queries = nn.Parameter(torch.randn(n_tokens, dna_dim) * 0.02)
        self.input_proj = nn.Linear(feature_dim, dna_dim)
        self.layers = nn.ModuleList(
            [_PerceiverLayer(dna_dim, n_heads) for _ in range(n_layers)]
        )

    def forward(self, patch_features: torch.Tensor) -> torch.Tensor:
        """patch_features: [B, P, feature_dim] → ДНК [B, n_tokens, dna_dim]."""
        batch_size = patch_features.shape[0]
        kv = self.input_proj(patch_features)
        dna = self.queries.unsqueeze(0).expand(batch_size, -1, -1)
        for layer in self.layers:
            dna = layer(dna, kv)
        return dna


def pooled_embedding(dna: torch.Tensor) -> torch.Tensor:
    """ДНК [B, N, d] → один вектор [B, d] (среднее по токенам) для контрастива/метрик."""
    return dna.mean(dim=1)


__all__ = ["DNACompressor", "pooled_embedding"]
