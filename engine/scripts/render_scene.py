"""Сцена → кадр. Тонкая обёртка над Blender: валидация здесь, рендер там.

Проверка описания и наличия файлов делается до запуска Blender — падать на опечатке
в JSON после сорока секунд импорта ассетов незачем.

    python scripts/render_scene.py --scene configs/mvp/scene.json --camera front
    python scripts/render_scene.py --scene configs/mvp/scene.json --all-cameras

Hydra здесь намеренно нет: один кадр — не прогон эксперимента. Трекингом обрастает
`run_matrix.py` на S7, где прогоняется вся матрица.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from worldgen.jsonread import ConfigValidationError
from worldgen.paths import ENGINE_ROOT, RUNS_DIR
from worldgen.render import BlenderNotFoundError, find_blender, run_blender_script
from worldgen.scene import check_assets_exist, load_scene
from worldgen.seed import set_seed

RENDER_MARKER = "WORLDGEN_RENDER_OK"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scene", default="configs/mvp/scene.json", help="JSON-описание сцены")
    parser.add_argument("--camera", help="id камеры; по умолчанию первая в описании")
    parser.add_argument("--all-cameras", action="store_true", help="отрендерить все ракурсы")
    parser.add_argument("--out-dir", default=str(RUNS_DIR / "s0"), help="куда класть кадры")
    parser.add_argument("--blender", help="путь к blender, если не находится сам")
    parser.add_argument("--save-blend", action="store_true", help="сохранить .blend рядом с кадром")
    parser.add_argument("--seed", type=int, default=1234, help="seed прогона")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    # Сам рендер EEVEE детерминирован; seed начнёт что-то значить с перерисовки (S2),
    # но фиксируем его с самого начала — прогон без set_seed в этом репозитории не бывает.
    set_seed(args.seed)

    scene_path = Path(args.scene)
    if not scene_path.is_absolute():
        scene_path = ENGINE_ROOT / scene_path

    try:
        scene = load_scene(scene_path)
    except ConfigValidationError as exc:
        print(f"описание сцены не прошло валидацию: {exc}", file=sys.stderr)
        return 2

    missing = check_assets_exist(scene)
    if missing:
        print(f"нет файлов ассетов: {', '.join(missing)}", file=sys.stderr)
        return 2

    if args.all_cameras:
        camera_ids = [c.id for c in scene.cameras]
    else:
        camera_ids = [args.camera or scene.cameras[0].id]
        scene.camera(camera_ids[0])  # ранняя проверка, что такой ракурс есть

    try:
        executable = find_blender(args.blender)
    except BlenderNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    print(f"blender: {executable}")

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ENGINE_ROOT / out_dir

    failed = 0
    for camera_id in camera_ids:
        out_path = out_dir / f"{scene.name}__{camera_id}.png"
        script_args = [
            "--scene",
            str(scene_path),
            "--camera",
            camera_id,
            "--out",
            str(out_path),
        ]
        if args.save_blend:
            script_args += ["--save-blend", str(out_path.with_suffix(".blend"))]

        result = run_blender_script("build_scene.py", script_args, blender=executable)
        if result.returncode != 0 or RENDER_MARKER not in result.stdout:
            failed += 1
            print(f"[{camera_id}] рендер не удался (код {result.returncode})", file=sys.stderr)
            print(result.stdout[-4000:], file=sys.stderr)
            print(result.stderr[-4000:], file=sys.stderr)
            continue
        print(f"[{camera_id}] {out_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
