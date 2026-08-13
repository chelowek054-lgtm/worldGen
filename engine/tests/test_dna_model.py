import pytest
import torch

from worldgen.dna.model import DNACompressor, pooled_embedding


def test_dna_compressor_output_shape():
    model = DNACompressor(feature_dim=32, dna_dim=16, n_tokens=8, n_layers=1, n_heads=4)
    patch_features = torch.rand(3, 10, 32)
    dna = model(patch_features)
    assert dna.shape == (3, 8, 16)


def test_dna_compressor_rejects_out_of_range_n_tokens():
    with pytest.raises(ValueError):
        DNACompressor(feature_dim=32, n_tokens=2)
    with pytest.raises(ValueError):
        DNACompressor(feature_dim=32, n_tokens=32)


def test_pooled_embedding_shape():
    dna = torch.rand(4, 8, 16)
    pooled = pooled_embedding(dna)
    assert pooled.shape == (4, 16)


def test_dna_compressor_is_trainable():
    model = DNACompressor(feature_dim=32, dna_dim=16, n_tokens=4, n_layers=1, n_heads=4)
    patch_features = torch.rand(2, 5, 32)
    dna = model(patch_features)
    loss = dna.sum()
    loss.backward()
    assert model.queries.grad is not None
    assert torch.any(model.queries.grad != 0)
