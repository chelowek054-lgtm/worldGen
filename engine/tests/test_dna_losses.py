import pytest
import torch

from worldgen.dna.losses import identity_margin, info_nce_loss


def test_info_nce_loss_lower_for_aligned_pairs():
    torch.manual_seed(0)
    base = torch.randn(8, 16)

    aligned_positive = base + torch.randn(8, 16) * 0.01
    misaligned_positive = base[torch.randperm(8)]

    aligned_loss = info_nce_loss(base, aligned_positive)
    misaligned_loss = info_nce_loss(base, misaligned_positive)

    assert aligned_loss.item() < misaligned_loss.item()


def test_info_nce_loss_requires_batch_of_at_least_two():
    with pytest.raises(ValueError):
        info_nce_loss(torch.rand(1, 8), torch.rand(1, 8))


def test_identity_margin_positive_for_separable_embeddings():
    torch.manual_seed(0)
    base = torch.randn(6, 16)
    positive = base + torch.randn(6, 16) * 0.01

    margin = identity_margin(base, positive)
    assert margin.item() > 0


def test_identity_margin_near_zero_for_random_embeddings():
    torch.manual_seed(1)
    anchor = torch.randn(200, 16)
    positive = torch.randn(200, 16)

    margin = identity_margin(anchor, positive)
    assert margin.item() < 0.2
