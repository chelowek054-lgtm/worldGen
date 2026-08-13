import torch

from worldgen.dna.backbone import RandomBackbone, build_backbone


def test_random_backbone_output_shape():
    backbone = RandomBackbone(feature_dim=32, seed=0)
    images = torch.rand(2, 3, 64, 64)
    features = backbone(images)
    assert features.shape == (2, 16, 32)  # 64/16=4 -> 4*4=16 патчей


def test_random_backbone_deterministic():
    a = RandomBackbone(feature_dim=16, seed=42)
    b = RandomBackbone(feature_dim=16, seed=42)
    images = torch.rand(1, 3, 32, 32)
    torch.testing.assert_close(a(images), b(images))


def test_random_backbone_frozen():
    backbone = RandomBackbone(feature_dim=16, seed=0)
    assert all(not p.requires_grad for p in backbone._proj.parameters())


def test_build_backbone_random():
    backbone = build_backbone({"name": "random", "feature_dim": 64, "seed": 1})
    assert backbone.feature_dim == 64


def test_build_backbone_unknown_raises():
    try:
        build_backbone({"name": "does-not-exist"})
    except ValueError:
        pass
    else:
        raise AssertionError("ожидался ValueError")
