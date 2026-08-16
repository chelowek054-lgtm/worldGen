"""Генерация болванки-персонажа для проверки сцены до появления настоящего ассета.

**Это не ассет MVP.** Настоящий герой — cel-персонаж с ригом (Roadmap-MVP 4.1);
болванка нужна только чтобы прогнать цепочку «JSON → сцена → кадр» и убедиться,
что свет, кадрирование и ракурсы описаны верно. Рига здесь нет: в срезе поза не
меняется, а болванку всё равно выбрасываем.

Асимметрия (нос и хвост) — намеренная: без неё фас, три четверти и профиль дают
почти одинаковую картинку, и ошибку в азимутах не заметить.

    blender -b --factory-startup --python make_proxy_asset.py -- --out data/assets/proxy.glb
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy

HEIGHT = 1.6  # метры: примерно рост будущего героя, чтобы кадрирование не переделывать


def _add(primitive, name: str, **kwargs):
    primitive(**kwargs)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def build_figure() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    add_cyl = bpy.ops.mesh.primitive_cylinder_add
    add_sphere = bpy.ops.mesh.primitive_uv_sphere_add

    _add(add_cyl, "torso", radius=0.17, depth=0.6, location=(0.0, 0.0, 1.02))
    _add(add_cyl, "hips", radius=0.15, depth=0.2, location=(0.0, 0.0, 0.68))
    _add(add_sphere, "head", radius=0.13, location=(0.0, 0.0, 1.47))
    _add(add_sphere, "neck", radius=0.06, location=(0.0, 0.0, 1.34))

    for side, x in (("l", -1.0), ("r", 1.0)):
        _add(add_cyl, f"arm_{side}", radius=0.05, depth=0.62, location=(x * 0.24, 0.0, 1.0))
        _add(add_cyl, f"leg_{side}", radius=0.07, depth=0.62, location=(x * 0.09, 0.0, 0.29))

    # Лицом к -Y — соглашение осей из worldgen.scene.schema.
    _add(
        bpy.ops.mesh.primitive_cone_add,
        "nose",
        radius1=0.03,
        depth=0.08,
        location=(0.0, -0.13, 1.45),
        rotation=(math.pi / 2, 0.0, 0.0),
    )
    _add(add_sphere, "ponytail", radius=0.08, location=(0.0, 0.14, 1.52))

    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects["torso"]
    bpy.ops.object.join()
    figure = bpy.context.active_object
    figure.name = "proxy_figure"
    bpy.ops.object.shade_smooth()

    # Без материала glTF импортируется белым и сливается с задником.
    material = bpy.data.materials.new("proxy_figure")
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = (0.72, 0.56, 0.47, 1.0)
        principled.inputs["Roughness"].default_value = 0.55
    figure.data.materials.append(material)

    # Начало координат — в ноль мира: у нормально собранного персонажа корень
    # в ступнях, и рендер не должен компенсировать чужую сборку.
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Собрать болванку-персонажа и выгрузить в glTF")
    parser.add_argument("--out", required=True, help="путь к .glb")
    args = parser.parse_args(argv)

    build_figure()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out_path), export_format="GLB")
    print(f"WORLDGEN_PROXY_OK {out_path.resolve()} height={HEIGHT}")


if __name__ == "__main__":
    main()
