# Мультивид-данные для ДНК-компрессора (holder)

Read-only обучающие данные для контрастива view-инвариантности из
[плана](../../../docs/archive/detailed-implementation-plan.md), задача **1.1**.
Сами данные **не коммитятся** в git — версионируются через DVC, как и
[`data/golden_set/`](../golden_set/README.md).

## Состав (заполняется в 1.1)

- Objaverse/Objaverse-XL рендеры: 8–24 вида на объект (только рендерер, не физдвижок).
- Реальный мультивид: `CO3D`, `MVImgNet`.
- Инстансы из видео, вырезанные через `SAM`.

## Формат манифеста

`manifest.yaml` в этом каталоге, пути — относительно файла манифеста:

```yaml
objects:
  - id: mug_01
    views: [renders/mug_01/view_00.png, renders/mug_01/view_01.png, ...]
  - id: chair_03
    views: [renders/chair_03/view_00.png, ...]
```

Загружается через `worldgen.dna.dataset.load_manifest`; каждый объект — минимум
2 вида (для пары anchor/positive в `MultiViewPairDataset`).

## Правила

- Пары «тот же объект, другой вид» верны на ручной выборке ≥ 96% (см. Проверка ✅
  шага 1.1); распределение ракурсов покрывает полусферу без больших дыр.
- Набор **read-only**, версия — через `dvc add` / `dvc status`.

> Пока это только holder-каталог. До наполнения (1.1) `worldgen/dna/` обучается на
> `SyntheticMultiViewDataset` — синтетических данных без файлов, только для проверки
> формы пайплайна (см. [engine/README.md](../../README.md)).
