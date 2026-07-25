"""Манифест золотого набора: описание состава, валидация, детерминированный хеш набора.

Хеш набора фиксируется в конфиге прогона (требование задачи 0.1) — по нему
верифицируется, что оценка шла ровно на той версии данных, что задумана.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GoldenSetManifest:
    version: int
    root: Path
    objects: list[dict[str, Any]] = field(default_factory=list)
    scenes: list[dict[str, Any]] = field(default_factory=list)
    physics: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> GoldenSetManifest:
        path = Path(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(
            version=int(data.get("version", 0)),
            root=path.parent,
            objects=list(data.get("objects") or []),
            scenes=list(data.get("scenes") or []),
            physics=list(data.get("physics") or []),
        )

    def relpaths(self) -> list[str]:
        """Все относительные пути файлов набора (виды, раскладки, клипы), отсортированные."""
        paths: list[str] = []
        for obj in self.objects:
            paths.extend(obj.get("views", []) or [])
        for scene in self.scenes:
            if scene.get("layout"):
                paths.append(scene["layout"])
        for clip in self.physics:
            if clip.get("clip"):
                paths.append(clip["clip"])
        return sorted(paths)

    def missing_files(self) -> list[str]:
        """Относительные пути, которых нет на диске (для валидации манифеста)."""
        return [rel for rel in self.relpaths() if not (self.root / rel).is_file()]

    def counts(self) -> dict[str, int]:
        return {
            "objects": len(self.objects),
            "scenes": len(self.scenes),
            "physics": len(self.physics),
            "files": len(self.relpaths()),
        }

    def set_hash(self) -> str:
        """Детерминированный sha256 набора: по парам (относительный путь, sha256 файла).

        Не зависит от порядка объявления и от абсолютного расположения набора.
        Отсутствующие файлы кодируются маркером `MISSING`, чтобы хеш неполного набора
        отличался от полного.
        """
        digest = hashlib.sha256()
        for rel in self.relpaths():
            digest.update(rel.encode("utf-8"))
            file_path = self.root / rel
            if file_path.is_file():
                digest.update(hashlib.sha256(file_path.read_bytes()).digest())
            else:
                digest.update(b"MISSING")
        return digest.hexdigest()


__all__ = ["GoldenSetManifest"]
