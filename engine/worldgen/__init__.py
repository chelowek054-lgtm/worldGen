"""World-Gen — нейросетевой движок генерации миров (ML-пайплайн).

Публичный API каркаса фазы 0: детерминизм (`set_seed`) и абстрактный трекинг
экспериментов (`build_tracker`, `Tracker`).
"""

from worldgen.seed import set_seed
from worldgen.tracking import Tracker, build_tracker

__version__ = "0.1.0"

__all__ = ["set_seed", "Tracker", "build_tracker", "__version__"]
