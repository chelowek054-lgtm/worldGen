# Журнал решений (decision log)

Каждый пройденный/непройденный go/no-go гейт и значимая развилка — одной записью, с
**числами** и **выводом**. Цель: чтобы «почему свернули сюда» всегда было прослеживаемо.
Статусы решений — в [Roadmap.md](Roadmap.md), шаги текущего среза — в
[Roadmap-MVP.md](Roadmap-MVP.md).

> Записи ниже — исторические и не переписываются. Ссылки в них могут указывать на
> документы, перенесённые в [archive](../archive/README.md); это нормально —
> журнал фиксирует, что было известно на момент решения.

## Шаблон записи

```
### YYYY-MM-DD · <ID гейта/шага> · <PASS | FAIL | PIVOT>
- **Контекст:** что проверяли и зачем.
- **Числа:** метрики/пороги (что получили vs что требовалось).
- **Вывод:** проходим дальше / чиним X / сворачиваем в фазу Y.
- **Артефакты:** ссылки на прогон, таблицу, коммит.
```

---

## Записи

### 2026-07-25 · setup · PASS
- **Контекст:** заведён markdown-трекер проекта (`STATUS.md` + этот журнал) поверх
  фазированного плана; выбран подход «md-в-репозитории» вместо внешнего трекера и вместо
  написания собственного (см. обсуждение — оверинжиниринг на текущей стадии).
- **Вывод:** ведём задачи в `STATUS.md`; на внешний трекер (GitHub Issues/Projects или
  Linear) переезжаем при появлении соисполнителей.
- **Артефакты:** `docs/base-plans/STATUS.md`, `docs/base-plans/decision-log.md`.

### 2026-07-25 · 0.0 · PASS
- **Контекст:** Definition of Ready — заведён ML-компонент `engine/` (PyTorch), отдельно
  от веб-стека. Реализованы: детерминизм (`set_seed` для random/numpy/torch), Hydra-конфиги,
  абстрактный трекинг (`Tracker`) с бэкендом MLflow, скрипт воспроизводимости `reproduce.py`,
  holder золотого набора.
- **Числа:** повтор того же конфига (seed=1234) → метрики совпадают **бит-в-бит**
  (`mean=0.5001288698394645`), т.е. в пределах гейта фазы 0 (±2%). Гейт: `pytest` 11/11,
  `ruff` clean, `mypy` clean.
- **Решения:**
  - Трекинг — **MLflow локально**; слой абстрактный (`tracking=noop` переключает на JSON).
  - MLflow 3.x снял file store → перешли на **SQLite-бэкенд** (`sqlite:///runs/mlflow.db`),
    добавлен регресс-тест.
  - Стек: core+dev установлены; `torch 2.13.0+cpu` (CUDA-сборка — под GPU-хост отдельно).
- **Вывод:** DoR выполнен, переходим к `0.1` (сбор золотого набора + `dvc add`).
- **Артефакты:** `engine/` (пакет `worldgen`, `scripts/reproduce.py`, `tests/`),
  `engine/README.md`.

### 2026-08-13 · 1.2a · PIVOT
- **Контекст:** по запросу пользователя заведён каркас `engine/worldgen/dna/`
  (ДНК-компрессор, задача 1.2) по аналогии со структурой pet-проекта OCR
  ([docs/developers/ocr-pipeline-lessons.md](../developers/ocr-pipeline-lessons.md)) —
  до прохождения гейта `0.G` и до наполнения золотого набора (0.1b) и мультивид-данных
  (1.1). Формально это опережает дисциплину плана («каждая фаза открывается только
  пройдя свой go/no-go»), но каркас не требует ни того, ни другого: тренировка идёт
  на `SyntheticMultiViewDataset` (детерминированные шаблон+шум, без файлов) и
  `RandomBackbone` (случайная проекция без сети/весов) — только проверка, что формы
  тензоров, лоссы, чекпоинты и Hydra-конфиг исправны.
- **Реализовано:** `backbone.py` (`FeatureBackbone` ABC + `RandomBackbone`/`Dinov3Backbone`
  + `build_backbone` — та же фабрика, что и у `tracking/`), `model.py` (Perceiver-ресемплер,
  N∈[4,16] токенов), `losses.py` (`info_nce_loss` + диагностика `identity_margin`),
  `dataset.py` (`MultiViewPairDataset` по манифесту + `SyntheticMultiViewDataset`),
  `trainer.py`, `predictor.py`, `checkpoints.py`; конфиги `configs/dna_config.yaml` +
  `configs/backbone/{random,dinov3}.yaml`; скрипт `scripts/train_dna.py`; holder
  `data/dna_train/`.
- **Числа:** `pytest` 39/39 (было 11), `ruff` clean, `mypy` clean (кроме одной
  предсуществовавшей ошибки типа `OmegaConf.to_container` в `reproduce.py`/`train_dna.py` —
  не регрессия). Смоук `train_dna.py train.epochs=1` — `loss` и `identity_margin`
  считаются и логируются (MLflow и `noop`).
- **Вывод:** каркас 1.2 закрыт как `1.2a`; `1.2b` (обучение на реальном DINOv3 +
  реальных данных) блокируется задачей `1.1`, как и раньше. `RandomBackbone`-прогоны
  не доказывают view-инвариантность — это заглушка форм, а не эксперимент; реальная
  Проверка ✅ шага 1.2 возможна только после `1.1` и `backbone=dinov3`.
- **Артефакты:** `engine/worldgen/dna/`, `engine/configs/dna_config.yaml`,
  `engine/configs/backbone/`, `engine/scripts/train_dna.py`, `engine/data/dna_train/`.

<!-- Следующая ожидаемая запись: 0.G — Go/No-Go фазы 0 (или 1.1, если данные найдутся раньше) -->
