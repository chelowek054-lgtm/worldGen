"""Сборка сцены внутри Blender по JSON-описанию.

Запускается подпроцессом (`worldgen.render.runner`), а не импортируется пакетом:
`bpy` существует только здесь. Скрипт **ничего не решает про сцену** — все позиции,
свет и ракурсы приходят из JSON (Roadmap 13.6). Здесь только перевод описания в
вызовы `bpy` — ровно та прослойка, которую придётся переписать, если рендерер
сменится на Godot.

Схему сцены импортируем из `worldgen.scene`: у пакета нет зависимостей сверх
стандартной библиотеки, поэтому он читается и питоном, встроенным в Blender.

    blender -b --factory-startup --python build_scene.py -- \
        --scene configs/mvp/scene.json --camera front --out runs/s0/front.png
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy

# engine/worldgen/render/blender/build_scene.py → parents[3] == engine/
ENGINE_ROOT = Path(__file__).resolve().parents[3]
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from worldgen.scene import (  # noqa: E402
    AssetRef,
    Camera,
    Environment,
    Light,
    RenderSettings,
    Scene,
    asset_path,
    load_scene,
)

GLTF_SUFFIXES = {".gltf", ".glb", ".vrm"}


# ------------------------------------------------------------------------ материалы


def _flat_material(name: str, color: tuple[float, float, float], roughness: float = 0.9):
    """Простой Principled. Cel-подача появится на S1 — здесь только читаемая база."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = (*color, 1.0)
        principled.inputs["Roughness"].default_value = roughness
    return material


# ----------------------------------------------------------------------- окружение


def build_world(env: Environment) -> None:
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (*env.world_color, 1.0)
        background.inputs["Strength"].default_value = env.world_strength
    bpy.context.scene.world = world


def build_environment(env: Environment) -> None:
    if env.ground_enabled:
        bpy.ops.mesh.primitive_plane_add(size=env.ground_size, location=(0.0, 0.0, 0.0))
        ground = bpy.context.active_object
        ground.name = "env/ground"
        ground.data.materials.append(_flat_material("env/ground", env.ground_color))

    if env.backdrop_enabled:
        # Вертикальная плоскость за героем: азимут 0 смотрит из -Y, значит задник в +Y.
        bpy.ops.mesh.primitive_plane_add(
            size=env.backdrop_size,
            location=(0.0, env.backdrop_distance, env.backdrop_size / 2.0),
            rotation=(math.pi / 2, 0.0, 0.0),
        )
        backdrop = bpy.context.active_object
        backdrop.name = "env/backdrop"
        backdrop.data.materials.append(_flat_material("env/backdrop", env.backdrop_color))


# --------------------------------------------------------------------------- ассеты


def import_asset(asset: AssetRef) -> list:
    """Импортировать ассет и вернуть созданные объекты, разложив их по имени ассета.

    Имена объектов префиксуются `id` ассета: по ним Cryptomatte строит манифест, и
    именно из них на S1 соберётся маска героя.
    """
    path = asset_path(asset)
    if not path.is_file():
        raise SystemExit(f"ассет {asset.id!r} не найден: {path}")
    suffix = path.suffix.lower()
    if suffix not in GLTF_SUFFIXES:
        raise SystemExit(
            f"ассет {asset.id!r}: поддерживается {sorted(GLTF_SUFFIXES)}, дано {suffix}"
        )

    collection = bpy.data.collections.new(asset.id)
    bpy.context.scene.collection.children.link(collection)

    bpy.ops.object.select_all(action="DESELECT")
    # .vrm — это glTF 2.0 с расширениями: штатный импортёр берёт геометрию и скелет,
    # игнорируя MToon. Нам это и нужно — облик собирается своим шейдингом (ADR 0002).
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = list(bpy.context.selected_objects)
    if not imported:
        raise SystemExit(f"ассет {asset.id!r}: импорт не дал ни одного объекта")

    for obj in imported:
        obj.name = f"{asset.id}/{obj.name}"
        for source in list(obj.users_collection):
            source.objects.unlink(obj)
        collection.objects.link(obj)

    for root in (obj for obj in imported if obj.parent is None):
        root.location = asset.location
        root.rotation_euler = tuple(math.radians(a) for a in asset.rotation_euler_deg)
        root.scale = (asset.scale, asset.scale, asset.scale)

    return imported


# ----------------------------------------------------------------------- свет и камера


def build_light(spec: Light) -> None:
    data = bpy.data.lights.new(name=spec.id, type=spec.type)
    data.energy = spec.energy
    data.color = spec.color
    if spec.type == "AREA":
        data.size = spec.size
    elif spec.type == "SUN":
        data.angle = math.radians(spec.size)  # угловой диаметр источника
    else:
        data.shadow_soft_size = spec.size

    obj = bpy.data.objects.new(name=spec.id, object_data=data)
    obj.location = spec.placement.location
    obj.rotation_euler = spec.placement.rotation_euler
    bpy.context.scene.collection.objects.link(obj)


def build_camera(spec: Camera):
    data = bpy.data.cameras.new(name=spec.id)
    # Вертикальная посадка угла: кадры портретные, и высота — то, чем кадрируют
    # стоящего героя. Иначе `fov_deg` менял бы смысл вместе с соотношением сторон.
    data.sensor_fit = "VERTICAL"
    data.angle = math.radians(spec.fov_deg)
    data.clip_start = spec.clip_start
    data.clip_end = spec.clip_end

    obj = bpy.data.objects.new(name=spec.id, object_data=data)
    obj.location = spec.placement.location
    obj.rotation_euler = spec.placement.rotation_euler
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.scene.camera = obj
    return obj


# ---------------------------------------------------------------------------- рендер


def apply_render_settings(settings: RenderSettings) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = settings.width
    scene.render.resolution_y = settings.height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = settings.film_transparent
    scene.eevee.taa_render_samples = settings.samples
    scene.view_settings.view_transform = settings.view_transform

    # Дата и длительность рендера уезжают в метаданные PNG и расходятся между
    # прогонами, хотя пиксели совпадают побайтово. Воспроизводимость — критерий
    # среза (Roadmap-MVP 4.6), и проверять её хешом файла надёжнее, чем разбором
    # пикселей. Остальные штампы (кадр, сцена, камера) детерминированы и полезны.
    scene.render.use_stamp_date = False
    scene.render.use_stamp_time = False
    scene.render.use_stamp_render_time = False


def render_still(out_path: Path) -> None:
    scene = bpy.context.scene
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if scene.render.film_transparent else "RGB"
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)


def build(scene_desc: Scene, camera_id: str) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    apply_render_settings(scene_desc.render)
    build_world(scene_desc.environment)
    build_environment(scene_desc.environment)
    for asset in scene_desc.assets:
        import_asset(asset)
    for light in scene_desc.lights:
        build_light(light)
    build_camera(scene_desc.camera(camera_id))


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Собрать сцену из JSON и отрендерить кадр")
    parser.add_argument("--scene", required=True, help="путь к JSON-описанию сцены")
    parser.add_argument("--camera", required=True, help="id камеры из описания")
    parser.add_argument("--out", required=True, help="путь к выходному PNG")
    parser.add_argument("--save-blend", help="дополнительно сохранить .blend для разбора глазами")
    args = parser.parse_args(argv)

    scene_desc = load_scene(args.scene)
    build(scene_desc, args.camera)

    if args.save_blend:
        blend_path = Path(args.save_blend)
        blend_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    render_still(Path(args.out))
    # Маркер для родительского процесса: по коду возврата Blender различить нечего.
    print(f"WORLDGEN_RENDER_OK {Path(args.out).resolve()}")


if __name__ == "__main__":
    main()
