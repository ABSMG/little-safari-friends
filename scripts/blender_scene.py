"""Low-poly procedural safari scene rendered by Blender."""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def get_args():
    raw = (
        sys.argv[sys.argv.index("--") + 1:]
        if "--" in sys.argv
        else []
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True)
    parser.add_argument("--output", required=True)

    return parser.parse_args(raw)


def mat(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.roughness = 0.8
    return material


def sphere(
    name,
    loc,
    scale,
    material,
    segments=20,
    rings=12
):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=loc
    )

    obj = bpy.context.object
    obj.name = name
    obj.scale = scale

    bpy.ops.object.shade_smooth()
    obj.data.materials.append(material)

    return obj


def rod(name, a, b, radius, material):
    start = Vector(a)
    end = Vector(b)
    direction = end - start

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=radius,
        depth=direction.length,
        location=(start + end) / 2
    )

    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat(
        "Z", "Y"
    )

    obj.data.materials.append(material)

    return obj


def label(body, loc, material):
    bpy.ops.object.text_add(
        location=loc,
        rotation=(math.radians(68), 0, 0)
    )

    obj = bpy.context.object
    obj.name = "Caption"
    obj.data.body = body
    obj.data.size = 0.29
    obj.data.align_x = "CENTER"
    obj.data.extrude = 0.002

    obj.data.materials.append(material)

    return obj


def create_lion(gold, mane, cream, dark):
    # Body and mane
    sphere(
        "Leo body",
        (-1.35, 0.6, 0.91),
        (0.56, 0.72, 0.42),
        gold
    )

    sphere(
        "Leo mane",
        (-1.35, 0.42, 1.55),
        (0.75, 0.62, 0.72),
        mane
    )

    sphere(
        "Leo face",
        (-1.35, 0.27, 1.63),
        (0.51, 0.46, 0.50),
        gold
    )

    sphere(
        "Leo muzzle",
        (-1.35, -0.14, 1.45),
        (0.30, 0.15, 0.20),
        cream
    )

    sphere(
        "Leo nose",
        (-1.35, -0.29, 1.54),
        (0.09, 0.045, 0.06),
        dark
    )

    # Eyes and ears
    for dx in (-0.2, 0.2):
        sphere(
            "Leo eye",
            (-1.35 + dx, -0.15, 1.77),
            (0.05, 0.04, 0.06),
            dark
        )

        sphere(
            "Leo ear",
            (-1.35 + dx * 1.9, 0.36, 1.99),
            (0.15, 0.13, 0.16),
            gold
        )

    # Four legs
    for x in (-1.68, -1.02):
        for y in (0.38, 0.86):
            sphere(
                "Leo leg",
                (x, y, 0.40),
                (0.14, 0.15, 0.34),
                gold
            )

    # Tail and tail tuft
    rod(
        "Leo tail",
        (-0.88, 1.25, 1.0),
        (-0.55, 1.52, 0.83),
        0.05,
        gold
    )

    sphere(
        "Leo tail tuft",
        (-0.52, 1.54, 0.82),
        (0.12, 0.12, 0.12),
        mane
    )


def create_elephant(grey, pink, dark):
    sphere(
        "Ellie body",
        (1.0, 1.0, 0.9),
        (0.62, 0.72, 0.5),
        grey
    )

    sphere(
        "Ellie head",
        (1.0, 0.55, 1.43),
        (0.46, 0.42, 0.45),
        grey
    )

    for dx in (-0.4, 0.4):
        sphere(
            "Ellie ear",
            (1 + dx, 0.53, 1.48),
            (0.29, 0.12, 0.34),
            pink
        )

        sphere(
            "Ellie eye",
            (1 + dx * 0.55, 0.12, 1.54),
            (0.045, 0.04, 0.05),
            dark
        )

    rod(
        "Ellie trunk",
        (1, 0.12, 1.32),
        (1, -0.02, 0.91),
        0.105,
        grey
    )

    for x in (0.68, 1.32):
        for y in (0.68, 1.3):
            sphere(
                "Ellie leg",
                (x, y, 0.39),
                (0.15, 0.16, 0.34),
                grey
            )


def create_giraffe(gold, brown):
    sphere(
        "Gigi body",
        (2.7, 0.9, 0.95),
        (0.42, 0.60, 0.4),
        gold
    )

    rod(
        "Gigi neck",
        (2.7, 0.72, 1.0),
        (2.7, 0.70, 2.05),
        0.16,
        gold
    )

    sphere(
        "Gigi head",
        (2.7, 0.65, 2.14),
        (0.28, 0.29, 0.28),
        gold
    )

    for dx in (-0.14, 0.14):
        rod(
            "Gigi ossicone",
            (2.7 + dx, 0.66, 2.34),
            (2.7 + dx, 0.66, 2.49),
            0.04,
            gold
        )

        sphere(
            "Gigi horn",
            (2.7 + dx, 0.66, 2.50),
            (0.06, 0.06, 0.06),
            brown
        )

    for x in (2.48, 2.92):
        for y in (0.65, 1.15):
            sphere(
                "Gigi leg",
                (x, y, 0.38),
                (0.10, 0.12, 0.33),
                gold
            )

    # Giraffe spots
    spots = [
        (2.54, 0.87),
        (2.82, 1.02),
        (2.76, 0.78),
        (2.62, 1.15)
    ]

    for x, z in spots:
        sphere(
            "Gigi spot",
            (x, 0.49, z),
            (0.06, 0.025, 0.07),
            brown,
            12,
            8
        )


def main():
    args = get_args()

    episode = json.loads(
        Path(args.episode).read_text(encoding="utf-8")
    )

    scene = bpy.context.scene

    # Clear the default scene.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Materials
    grass = mat(
        "Savanna grass",
        (0.40, 0.62, 0.22)
    )

    gold = mat(
        "Leo and Gigi gold",
        (1.0, 0.60, 0.13)
    )

    mane = mat(
        "Lion mane",
        (0.42, 0.18, 0.06)
    )

    cream = mat(
        "Muzzle cream",
        (1.0, 0.85, 0.59)
    )

    dark = mat(
        "Dark eyes",
        (0.035, 0.025, 0.02)
    )

    grey = mat(
        "Ellie grey",
        (0.48, 0.55, 0.60)
    )

    pink = mat(
        "Inner ears",
        (0.9, 0.36, 0.40)
    )

    brown = mat(
        "Spots and tree",
        (0.38, 0.17, 0.06)
    )

    white = mat(
        "Clouds",
        (1.0, 1.0, 1.0)
    )

    caption_material = mat(
        "Caption",
        (0.04, 0.10, 0.07)
    )

    orange = mat(
        "Mango",
        (1.0, 0.30, 0.025)
    )

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=200)

    ground = bpy.context.object
    ground.name = "Savanna"
    ground.data.materials.append(grass)

    # Acacia tree
    rod(
        "Acacia trunk",
        (3.7, 1.8, 0),
        (3.7, 1.8, 2.2),
        0.18,
        brown
    )

    canopy_parts = [
        (3.7, 2.5, (1.2, 0.45, 0.34)),
        (3.0, 2.32, (0.7, 0.4, 0.25)),
        (4.4, 2.32, (0.7, 0.4, 0.25))
    ]

    for x, z, size in canopy_parts:
        sphere(
            "Acacia canopy",
            (x, 1.8, z),
            size,
            grass
        )

    # Mangoes
    for x in (-1.1, -0.5, 0.1):
        sphere(
            "Mango",
            (x, -0.8, 0.16),
            (0.16, 0.20, 0.14),
            orange
        )

        sphere(
            "Mango leaf",
            (x + 0.05, -0.79, 0.28),
            (0.06, 0.025, 0.025),
            grass,
            12,
            8
        )

    # Characters
    create_lion(gold, mane, cream, dark)
    create_elephant(grey, pink, dark)
    create_giraffe(gold, brown)

    # Clouds
    clouds = [
        (-3.4, 2.7, 5.1),
        (0.1, 3.0, 5.5),
        (3.7, 3.1, 5.1)
    ]

    for cx, cy, cz in clouds:
        pieces = [
            (-0.3, 0, 0.34),
            (0, 0.1, 0.42),
            (0.32, 0.02, 0.30)
        ]

        for dx, dz, size in pieces:
            sphere(
                "Cloud",
                (cx + dx, cy, cz + dz),
                (size, 0.16, size * 0.5),
                white,
                16,
                8
            )

    # Captions
    captions = []

    for index, item in enumerate(episode["scenes"]):
        obj = label(
            item.get("caption", ""),
            (0, -2.45, 3.35),
            caption_material
        )

        obj.name = f"Caption_{index}"
        captions.append((obj, item))

    # Camera
    bpy.ops.object.camera_add(
        location=(0, -10.5, 5.0)
    )

    camera = bpy.context.object

    direction = (
        Vector((0, 0.2, 1.25))
        - camera.location
    )

    camera.rotation_euler = direction.to_track_quat(
        "-Z", "Y"
    ).to_euler()

    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10.3
    scene.camera = camera

    # Lighting
    bpy.ops.object.light_add(
        type="AREA",
        location=(-4, -5, 8)
    )

    key_light = bpy.context.object
    key_light.data.energy = 1400
    key_light.data.size = 8

    bpy.ops.object.light_add(
        type="AREA",
        location=(4, 2, 6)
    )

    fill_light = bpy.context.object
    fill_light.data.energy = 650
    fill_light.data.size = 6

    # Render settings
    scene.world.color = (0.35, 0.52, 0.70)

    if bpy.app.version >= (4, 0, 0):
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"

    scene.render.resolution_x = int(
        episode.get("width", 1280)
    )

    scene.render.resolution_y = int(
        episode.get("height", 720)
    )

    # Faster rendering for GitHub Actions CPU runners.
    scene.render.resolution_percentage = int(
        episode.get("resolution_percentage", 75)
    )

    # Reduce Eevee rendering samples from the default 64 to 8.
    # This significantly reduces rendering time.
    try:
        if hasattr(scene, "eevee") and hasattr(
            scene.eevee, "taa_render_samples"
        ):
            scene.eevee.taa_render_samples = int(
                episode.get("render_samples", 8)
            )
    except (AttributeError, TypeError, ValueError) as error:
        print(
            f"Could not configure Eevee samples: {error}",
            flush=True,
        )

    # Avoid unnecessary subdivision work.
    try:
        scene.render.use_simplify = True
        scene.render.simplify_subdivision = 0
    except (AttributeError, TypeError):
        pass

    print(
        f"Rendering at {scene.render.resolution_x}x"
        f"{scene.render.resolution_y}, "
        f"{scene.render.resolution_percentage}% scale; "
        f"samples={episode.get('render_samples', 8)}",
        flush=True,
    )

    scene.render.fps = int(episode.get("fps", 24))
    scene.frame_start = 1

    scene.frame_end = (
        int(episode.get("duration_seconds", 32))
        * scene.render.fps
    )

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"

    scene.render.filepath = str(
        Path(args.output).resolve()
    )

    scene.view_settings.view_transform = "Standard"

    # Gentle bouncing animation for Leo.
    for name in ("Leo face", "Leo mane"):
        obj = bpy.data.objects.get(name)

        if obj is None:
            continue

        base = obj.location.copy()

        obj.keyframe_insert(
            data_path="location",
            frame=1
        )

        obj.location.z += 0.09

        obj.keyframe_insert(
            data_path="location",
            frame=scene.render.fps * 2
        )

        obj.location = base

        obj.keyframe_insert(
            data_path="location",
            frame=scene.render.fps * 4
        )

    # Show each caption during its assigned time interval.
    for obj, item in captions:
        start = max(
            1,
            int(item.get("start", 0) * scene.render.fps) + 1
        )

        end = min(
            scene.frame_end,
            int(item.get("end", 32) * scene.render.fps)
        )

        obj.hide_render = True
        obj.keyframe_insert(
            data_path="hide_render",
            frame=1
        )

        obj.hide_render = False
        obj.keyframe_insert(
            data_path="hide_render",
            frame=start
        )

        obj.hide_render = True

        obj.keyframe_insert(
            data_path="hide_render",
            frame=min(scene.frame_end, end + 1)
        )

        if obj.animation_data and obj.animation_data.action:
            for curve in obj.animation_data.action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = "CONSTANT"

    # Render the animation.
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
