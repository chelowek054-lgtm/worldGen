"""CLI: проверка пересечения золотого набора с обучающими источниками (гейт 0.1).

Пример:
    python scripts/check_overlap.py --eval data/golden_set --train /path/to/train_a /path/to/train_b
    python scripts/check_overlap.py --eval data/golden_set --train ./train --threshold 5

Код возврата: 0 — пересечений нет (гейт пройден); 1 — найдены коллизии.
"""

from __future__ import annotations

import argparse
import sys

from worldgen.eval.overlap import DEFAULT_THRESHOLD, find_collisions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Проверка пересечения eval-набора с train.")
    parser.add_argument("--eval", required=True, help="каталог золотого набора")
    parser.add_argument("--train", required=True, nargs="+", help="каталог(и) train-источников")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    args = parser.parse_args(argv)

    collisions = find_collisions(args.eval, args.train, threshold=args.threshold)

    if not collisions:
        print(f"[overlap] коллизий нет (threshold={args.threshold}); гейт 0.1 ок")
        return 0

    print(f"[overlap] НАЙДЕНО коллизий: {len(collisions)} (threshold={args.threshold})")
    for c in collisions:
        print(f"  d={c.distance}  {c.eval_path}  ~=  {c.train_path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
