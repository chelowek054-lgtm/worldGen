from pathlib import Path

import torch

from worldgen.dna.checkpoints import Checkpoint, load_checkpoint, save_checkpoint
from worldgen.dna.model import DNACompressor


def test_checkpoint_roundtrip(tmp_path: Path):
    model = DNACompressor(feature_dim=16, dna_dim=8, n_tokens=4, n_layers=1, n_heads=2)
    path = tmp_path / "nested" / "model.pt"

    save_checkpoint(
        path,
        Checkpoint(
            model_state_dict=model.state_dict(),
            config={"dna_dim": 8, "n_tokens": 4},
            epoch=3,
            metric=0.42,
        ),
    )
    assert path.is_file()

    loaded = load_checkpoint(path)
    assert loaded.epoch == 3
    assert loaded.metric == 0.42
    assert loaded.config == {"dna_dim": 8, "n_tokens": 4}

    restored = DNACompressor(feature_dim=16, dna_dim=8, n_tokens=4, n_layers=1, n_heads=2)
    restored.load_state_dict(loaded.model_state_dict)

    patch_features = torch.rand(1, 5, 16)
    torch.testing.assert_close(model(patch_features), restored(patch_features))
