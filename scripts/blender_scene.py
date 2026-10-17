"""Premium hybrid animated safari scene rendered by Blender.

Features:
- Leo the lion, Ellie the elephant and Gigi the giraffe.
- Procedural safari environment, acacia tree, mangoes and clouds.
- Improved materials, lighting, shadows and color management.
- Character movement, head/body bounce, tail and leg animation.
- Animated camera movement.
- Episode-driven captions.
- Configurable resolution, samples, duration and frame rate.
- MP4/H.264 output suitable for GitHub Actions automation.
- Blender 3.x and 4.x color-management compatibility.
- Compatible handling of weighted-normal modifiers.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


# ---------------------------------------------------------
# COMMAND-LINE ARGUMENTS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# MATERIALS
# ---------------------------------------------------------

def mat(
    name,
    color,
    roughness=0.72,
    metallic=0.0,
    subsurface=0.0
):
    material = bpy.data.materials.get(name)

    if material is None:
        material = bpy.data.materials.new(name)

    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True

    bsdf = material.node_tree.nodes.get("Principled BSDF")

    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (
                *color,
                1.0
            )

        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness

        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic

        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs[
                "Subsurface Weight"
            ].default_value = subsurface
        elif "Subsurface" in bsdf.inputs:
            bsdf.inputs[
                "Subsurface"
            ].default_value = subsurface

    material.roughness = roughness

    return material


# ---------------------------------------------------------
# BASIC PROCEDURAL OBJECTS
# ---------------------------------------------------------

def sphere(
    name,
    loc,
    scale,
    material,
    segments=32,
    rings=20
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


def rod(name, a, b, radius, material, vertices=20):
    start = Vector(a)
    end = Vector(b)
    direction = end - start

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=max(direction.length, 0.001),
        location=(start + end) / 2
    )

    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat(
        "Z",
        "Y"
    )

    obj.data.materials.append(material)

    bevel = obj.modifiers.new(
        name="Soft rounded edges",
        type="BEVEL"
    )
    bevel.width = min(radius * 0.22, 0.035)
    bevel.segments = 3

    # Blender 3.x compatibility:
    # Weighted Normal modifiers can warn when Auto Smooth
    # is disabled. Enable it when this property exists.
    try:
        if hasattr(obj.data, "use_auto_smooth"):
            obj.data.use_auto_smooth = True
    except (AttributeError, TypeError, ValueError):
        pass

    # Keep the weighted-normal modifier where supported.
    # Avoid stopping the scene build if a Blender version
    # does not support the modifier.
    try:
        obj.modifiers.new(
            name="Weighted corner normals",
            type="WEIGHTED_NORMAL"
        )
    except (RuntimeError, TypeError, ValueError):
        pass

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
    obj.data.bevel_depth = 0.001
    obj.data.bevel_resolution = 2

    obj.data.materials.append(material)

    return obj


# ---------------------------------------------------------
# ANIMATION HELPERS
# ---------------------------------------------------------

def smooth_animation(obj):
    if not obj.animation_data:
        return

    action = obj.animation_data.action

    if not action:
        return

    # Blender 3.x exposes action.fcurves directly.
    # Guard this section for compatibility with newer APIs.
    try:
        curves = action.fcurves
    except (AttributeError, TypeError):
        return

    for curve in curves:
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"


def animate_bounce(obj, start_frame, end_frame, amount=0.06):
    """Create a gentle, repeating vertical bounce."""

    base_z = obj.location.z
    middle = (start_frame + end_frame) // 2

    obj.location.z = base_z
    obj.keyframe_insert(
        data_path="location",
        frame=start_frame
    )

    obj.location.z = base_z + amount
    obj.keyframe_insert(
        data_path="location",
        frame=middle
    )

    obj.location.z = base_z
    obj.keyframe_insert(
        data_path="location",
        frame=end_frame
    )

    smooth_animation(obj)


def animate_swing(obj, start_frame, end_frame, angle=0.16):
    """Animate a small rotation around the object's local X axis."""

    base_rotation = obj.rotation_euler.copy()
    middle = (start_frame + end_frame) // 2

    obj.rotation_euler = base_rotation
    obj.keyframe_insert(
        data_path="rotation_euler",
        frame=start_frame
    )

    obj.rotation_euler.x = base_rotation.x + angle
    obj.keyframe_insert(
        data_path="rotation_euler",
        frame=middle
    )

    obj.rotation_euler = base_rotation
    obj.keyframe_insert(
        data_path="rotation_euler",
        frame=end_frame
    )

    smooth_animation(obj)


def animate_character_parts(prefix, start_frame, end_frame, fps):
    """Animate body parts individually for a more lively scene."""

    objects = [
        obj for obj in bpy.context.scene.objects
        if obj.name.startswith(prefix)
    ]

    for obj in objects:
        name = obj.name.lower()

        if any(part in name for part in (
            "body",
            "head",
            "face",
            "mane",
            "neck"
        )):
            amount = 0.045 if "body" in name else 0.065

            if "neck" in name:
                amount = 0.035

            animate_bounce(
                obj,
                start_frame,
                end_frame,
                amount
            )

        elif any(part in name for part in (
            "leg",
            "tail",
            "trunk",
            "ear"
        )):
            angle = 0.12

            if "tail" in name:
                angle = 0.24
            elif "trunk" in name:
                angle = 0.20
            elif "ear" in name:
                angle = 0.10

            animate_swing(
                obj,
                start_frame,
                end_frame,
                angle
            )


def animate_camera(camera, start_frame, end_frame):
    """Subtle cinematic camera push-in and pull-back."""

    base_location = camera.location.copy()
    base_scale = camera.data.ortho_scale

    middle = (start_frame + end_frame) // 2

    camera.location = base_location
    camera.data.ortho_scale = base_scale

    camera.keyframe_insert(
        data_path="location",
        frame=start_frame
    )
    camera.data.keyframe_insert(
        data_path="ortho_scale",
        frame=start_frame
    )

    camera.location.y += 0.35
    camera.location.z += 0.12
    camera.data.ortho_scale = base_scale * 0.96

    camera.keyframe_insert(
        data_path="location",
        frame=middle
    )
    camera.data.keyframe_insert(
        data_path="ortho_scale",
        frame=middle
    )

    camera.location = base_location
    camera.data.ortho_scale = base_scale

    camera.keyframe_insert(
        data_path="location",
        frame=end_frame
    )
    camera.data.keyframe_insert(
        data_path="ortho_scale",
        frame=end_frame
    )

    smooth_animation(camera)
    smooth_animation(camera.data)


# ---------------------------------------------------------
# LION: LEO
# ---------------------------------------------------------

def create_lion(gold, mane, cream, dark, white):
    # Main body.
    sphere(
        "Leo body",
        (-1.35, 0.6, 0.91),
        (0.58, 0.72, 0.44),
        gold
    )

    # Mane and face.
    sphere(
        "Leo mane",
        (-1.35, 0.42, 1.55),
        (0.78, 0.64, 0.74),
        mane,
        40,
        28
    )

    sphere(
        "Leo face",
        (-1.35, 0.25, 1.64),
        (0.52, 0.47, 0.51),
        gold,
        40,
        28
    )

    sphere(
        "Leo muzzle",
        (-1.35, -0.14, 1.45),
        (0.31, 0.16, 0.21),
        cream
    )

    sphere(
        "Leo nose",
        (-1.35, -0.29, 1.54),
        (0.09, 0.045, 0.06),
        dark
    )

    # Eyes with highlights.
    for dx in (-0.20, 0.20):
        sphere(
            "Leo eye",
            (-1.35 + dx, -0.15, 1.78),
            (0.065, 0.045, 0.075),
            dark
        )

        sphere(
            "Leo eye highlight",
            (-1.35 + dx - 0.015, -0.192, 1.805),
            (0.018, 0.012, 0.022),
            white,
            16,
            10
        )

        sphere(
            "Leo ear",
            (-1.35 + dx * 1.9, 0.36, 1.99),
            (0.16, 0.14, 0.17),
            gold
        )

        sphere(
            "Leo inner ear",
            (-1.35 + dx * 1.9, 0.235, 2.0),
            (0.085, 0.035, 0.09),
            mane
        )

    # Four legs with separate names for animation.
    for index, x in enumerate((-1.68, -1.02)):
        for side_index, y in enumerate((0.38, 0.86)):
            sphere(
                f"Leo leg {index}_{side_index}",
                (x, y, 0.40),
                (0.15, 0.16, 0.34),
                gold
            )

            sphere(
                f"Leo paw {index}_{side_index}",
                (x, y - 0.025, 0.16),
                (0.17, 0.18, 0.10),
                cream
            )

    # Tail and tuft.
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
        (0.13, 0.12, 0.13),
        mane
    )

    # Mane tufts add silhouette detail.
    for index, angle in enumerate(
        (0.0, 0.8, 1.6, 2.4, 3.2, 4.0, 4.8, 5.6)
    ):
        x = -1.35 + math.cos(angle) * 0.68
        z = 1.55 + math.sin(angle) * 0.65

        sphere(
            f"Leo mane tuft {index}",
            (x, 0.42, z),
            (0.16, 0.14, 0.20),
            mane,
            20,
            12
        )


# ---------------------------------------------------------
# ELEPHANT: ELLIE
# ---------------------------------------------------------

def create_elephant(grey, pink, dark, white):
    sphere(
        "Ellie body",
        (1.0, 1.0, 0.9),
        (0.64, 0.74, 0.52),
        grey,
        36,
        24
    )

    sphere(
        "Ellie head",
        (1.0, 0.55, 1.43),
        (0.48, 0.43, 0.46),
        grey,
        36,
        24
    )

    for dx in (-0.4, 0.4):
        sphere(
            "Ellie ear",
            (1 + dx, 0.53, 1.48),
            (0.31, 0.13, 0.35),
            grey
        )

        sphere(
            "Ellie inner ear",
            (1 + dx, 0.405, 1.48),
            (0.22, 0.045, 0.26),
            pink
        )

    for dx in (-0.20, 0.20):
        sphere(
            "Ellie eye",
            (1 + dx, 0.12, 1.55),
            (0.055, 0.045, 0.06),
            dark
        )

        sphere(
            "Ellie eye highlight",
            (1 + dx - 0.012, 0.078, 1.57),
            (0.016, 0.012, 0.018),
            white,
            16,
            10
        )

    # Trunk segments provide a softer, articulated appearance.
    rod(
        "Ellie trunk",
        (1.0, 0.12, 1.32),
        (1.0, -0.02, 0.91),
        0.105,
        grey,
        24
    )

    sphere(
        "Ellie trunk tip",
        (1.0, -0.025, 0.90),
        (0.12, 0.12, 0.12),
        grey
    )

    # Small tusks.
    ivory = cream_material()

    for dx in (-0.13, 0.13):
        rod(
            "Ellie tusk",
            (1.0 + dx, 0.04, 1.24),
            (1.0 + dx, -0.02, 1.08),
            0.035,
            ivory,
            12
        )

    for index, x in enumerate((0.68, 1.32)):
        for side_index, y in enumerate((0.68, 1.3)):
            sphere(
                f"Ellie leg {index}_{side_index}",
                (x, y, 0.39),
                (0.16, 0.17, 0.34),
                grey
            )

            sphere(
                f"Ellie foot {index}_{side_index}",
                (x, y - 0.02, 0.15),
                (0.18, 0.19, 0.10),
                grey
            )


def cream_material():
    """Create a reusable ivory material for small tusks."""

    material = bpy.data.materials.get("Ivory tusks")

    if material:
        return material

    return mat(
        "Ivory tusks",
        (0.96, 0.88, 0.68),
        roughness=0.4
    )


# ---------------------------------------------------------
# GIRAFFE: GIGI
# ---------------------------------------------------------

def create_giraffe(gold, brown, dark, white):
    sphere(
        "Gigi body",
        (2.7, 0.9, 0.95),
        (0.44, 0.62, 0.42),
        gold
    )

    rod(
        "Gigi neck",
        (2.7, 0.72, 1.0),
        (2.7, 0.70, 2.05),
        0.17,
        gold,
        24
    )

    sphere(
        "Gigi head",
        (2.7, 0.65, 2.14),
        (0.30, 0.30, 0.29),
        gold
    )

    sphere(
        "Gigi muzzle",
        (2.7, 0.37, 2.06),
        (0.22, 0.13, 0.14),
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
            (0.065, 0.065, 0.065),
            brown
        )

    for dx in (-0.14, 0.14):
        sphere(
            "Gigi eye",
            (2.7 + dx, 0.37, 2.19),
            (0.045, 0.035, 0.05),
            dark
        )

        sphere(
            "Gigi eye highlight",
            (2.7 + dx - 0.01, 0.337, 2.205),
            (0.013, 0.01, 0.015),
            white,
            16,
            10
        )

    # Four legs.
    for index, x in enumerate((2.48, 2.92)):
        for side_index, y in enumerate((0.65, 1.15)):
            sphere(
                f"Gigi leg {index}_{side_index}",
                (x, y, 0.38),
                (0.11, 0.13, 0.33),
                gold
            )

    # Distinctive brown giraffe spots.
    spots = [
        (2.54, 0.87),
        (2.82, 1.02),
        (2.76, 0.78),
        (2.62, 1.15),
        (2.68, 1.00),
        (2.83, 0.84),
        (2.58, 1.06)
    ]

    for index, (x, z) in enumerate(spots):
        sphere(
            f"Gigi spot {index}",
            (x, 0.49, z),
            (0.075, 0.03, 0.08),
            brown,
            16,
            10
        )


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------

def create_environment(grass, brown, white, orange):
    # Ground plane.
    bpy.ops.mesh.primitive_plane_add(size=200)

    ground = bpy.context.object
    ground.name = "Savanna"
    ground.data.materials.append(grass)

    # A small procedural grass patch adds foreground detail.
    grass_blades = mat(
        "Foreground grass blades",
        (0.24, 0.43, 0.12)
    )

    for index in range(28):
        x = -4.5 + (index % 14) * 0.68
        y = -1.4 - (index // 14) * 0.55

        rod(
            f"Grass blade {index}",
            (x, y, 0.02),
            (x + 0.06, y, 0.18 + (index % 3) * 0.04),
            0.018,
            grass_blades,
            8
        )

    # Acacia tree.
    rod(
        "Acacia trunk",
        (3.7, 1.8, 0),
        (3.7, 1.8, 2.2),
        0.18,
        brown
    )

    canopy_material = mat(
        "Acacia foliage",
        (0.20, 0.39, 0.13),
        roughness=0.9
    )

    canopy_parts = [
        (3.7, 2.5, (1.2, 0.45, 0.34)),
        (3.0, 2.32, (0.7, 0.4, 0.25)),
        (4.4, 2.32, (0.7, 0.4, 0.25))
    ]

    for index, (x, z, size) in enumerate(canopy_parts):
        sphere(
            f"Acacia canopy {index}",
            (x, 1.8, z),
            size,
            canopy_material
        )

    # Mangoes and leaves.
    for index, x in enumerate((-1.1, -0.5, 0.1)):
        sphere(
            f"Mango {index}",
            (x, -0.8, 0.16),
            (0.16, 0.20, 0.14),
            orange
        )

        sphere(
            f"Mango leaf {index}",
            (x + 0.05, -0.79, 0.28),
            (0.06, 0.025, 0.025),
            grass,
            16,
            10
        )

    # Clouds.
    for cloud_index, (cx, cy, cz) in enumerate([
        (-3.4, 2.7, 5.1),
        (0.1, 3.0, 5.5),
        (3.7, 3.1, 5.1)
    ]):
        pieces = [
            (-0.3, 0, 0.34),
            (0, 0.1, 0.42),
            (0.32, 0.02, 0.30)
        ]

        for part_index, (dx, dz, size) in enumerate(pieces):
            sphere(
                f"Cloud {cloud_index}_{part_index}",
                (cx + dx, cy, cz + dz),
                (size, 0.16, size * 0.5),
                white,
                20,
                12
            )


# ---------------------------------------------------------
# LIGHTING AND CAMERA
# ---------------------------------------------------------

def create_camera(scene):
    bpy.ops.object.camera_add(
        location=(0, -10.5, 5.0)
    )

    camera = bpy.context.object
    camera.name = "Cinematic Camera"

    direction = (
        Vector((0, 0.2, 1.25))
        - camera.location
    )

    camera.rotation_euler = direction.to_track_quat(
        "-Z",
        "Y"
    ).to_euler()

    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10.3
    camera.data.lens = 45

    scene.camera = camera

    return camera


def create_lighting():
    # Warm key light.
    bpy.ops.object.light_add(
        type="AREA",
        location=(-4, -5, 8)
    )

    key_light = bpy.context.object
    key_light.name = "Warm sunset key light"
    key_light.data.energy = 1600
    key_light.data.shape = "DISK"
    key_light.data.size = 7
    key_light.data.color = (1.0, 0.79, 0.57)

    # Cooler fill light.
    bpy.ops.object.light_add(
        type="AREA",
        location=(4, 2, 6)
    )

    fill_light = bpy.context.object
    fill_light.name = "Soft sky fill light"
    fill_light.data.energy = 800
    fill_light.data.shape = "DISK"
    fill_light.data.size = 6
    fill_light.data.color = (0.67, 0.81, 1.0)

    # Back/rim light for character separation.
    bpy.ops.object.light_add(
        type="AREA",
        location=(1.5, 4.0, 5.5)
    )

    rim_light = bpy.context.object
    rim_light.name = "Golden rim light"
    rim_light.data.energy = 1100
    rim_light.data.size = 4
    rim_light.data.color = (1.0, 0.62, 0.31)


# ---------------------------------------------------------
# CAPTION TIMING
# ---------------------------------------------------------

def configure_captions(scene, captions):
    for obj, item in captions:
        start = max(
            1,
            int(item.get("start", 0) * scene.render.fps) + 1
        )

        end = min(
            scene.frame_end,
            int(item.get("end", 32) * scene.render.fps)
        )

        if end < start:
            end = start

        # Hide captions before their assigned scene.
        obj.hide_render = True
        obj.keyframe_insert(
            data_path="hide_render",
            frame=1
        )

        obj.hide_render = True
        obj.keyframe_insert(
            data_path="hide_render",
            frame=max(1, start - 1)
        )

        # Show caption during its assigned interval.
        obj.hide_render = False
        obj.keyframe_insert(
            data_path="hide_render",
            frame=start
        )

        # Hide caption immediately after the interval.
        obj.hide_render = True
        obj.keyframe_insert(
            data_path="hide_render",
            frame=min(scene.frame_end, end + 1)
        )

        if obj.animation_data and obj.animation_data.action:
            try:
                curves = obj.animation_data.action.fcurves
            except (AttributeError, TypeError):
                curves = []

            for curve in curves:
                for point in curve.keyframe_points:
                    point.interpolation = "CONSTANT"


# ---------------------------------------------------------
# COLOR MANAGEMENT
# ---------------------------------------------------------

def configure_color_management(scene):
    """Select only color-management options supported by Blender."""

    view_settings = scene.view_settings

    # Get supported view transforms for the installed Blender.
    try:
        available_transforms = [
            item.name
            for item in (
                bpy.types.ColorManagedViewSettings
                .bl_rna.properties["view_transform"].enum_items
            )
        ]
    except (AttributeError, TypeError, ValueError):
        available_transforms = []

    # Prefer AgX when available, then Filmic, then Standard.
    # Blender 3.0.1 may not provide AgX.
    for transform_name in (
        "AgX",
        "Filmic",
        "Standard"
    ):
        if transform_name not in available_transforms:
            continue

        try:
            view_settings.view_transform = transform_name
            print(
                f"Color management: view transform = "
                f"{transform_name}",
                flush=True
            )
            break
        except (AttributeError, TypeError, ValueError):
            continue

    # Discover supported looks. Some Blender versions only
    # expose "None", so never assign an unavailable look.
    try:
        available_looks = [
            item.name
            for item in (
                bpy.types.ColorManagedViewSettings
                .bl_rna.properties["look"].enum_items
            )
        ]
    except (AttributeError, TypeError, ValueError):
        available_looks = []

    preferred_looks = (
        "AgX - Medium High Contrast",
        "Medium High Contrast",
        "Medium High Contrast Look",
        "None",
    )

    selected_look = False

    for look_name in preferred_looks:
        if look_name not in available_looks:
            continue

        try:
            view_settings.look = look_name
            print(
                f"Color management: look = {look_name}",
                flush=True
            )
            selected_look = True
            break
        except (AttributeError, TypeError, ValueError):
            continue

    if not selected_look:
        print(
            "Color management: keeping Blender's supported "
            "default look.",
            flush=True
        )

    # Safe exposure and gamma defaults.
    try:
        view_settings.exposure = 0.0
        view_settings.gamma = 1.0
    except (AttributeError, TypeError, ValueError) as error:
        print(
            f"Color management exposure/gamma warning: {error}",
            flush=True
        )


# ---------------------------------------------------------
# RENDER SETTINGS
# ---------------------------------------------------------

def configure_render_engine(scene):
    """Configure an Eevee engine available in this Blender version."""

    if bpy.app.version >= (4, 0, 0):
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"

    print(
        f"Render engine: {scene.render.engine}",
        flush=True
    )


def configure_eevee_samples(scene, samples):
    """Set Eevee sample count when supported by the engine."""

    try:
        if hasattr(scene, "eevee") and hasattr(
            scene.eevee,
            "taa_render_samples"
        ):
            scene.eevee.taa_render_samples = samples
            print(
                f"Eevee render samples: {samples}",
                flush=True
            )
    except (AttributeError, TypeError, ValueError) as error:
        print(
            f"Could not configure Eevee samples: {error}",
            flush=True
        )


def configure_shadow_features(scene):
    """Enable ambient occlusion on Blender versions exposing it."""

    try:
        if hasattr(scene, "eevee"):
            if hasattr(scene.eevee, "use_gtao"):
                scene.eevee.use_gtao = True

            if hasattr(scene.eevee, "gtao_distance"):
                scene.eevee.gtao_distance = 3

            if hasattr(scene.eevee, "gtao_factor"):
                scene.eevee.gtao_factor = 1.25
    except (AttributeError, TypeError, ValueError) as error:
        print(
            f"Optional ambient-occlusion warning: {error}",
            flush=True
        )


def configure_video_output(scene, output_path):
    """Configure the MP4/H.264 animation output."""

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"

    try:
        scene.render.ffmpeg.constant_rate_factor = "HIGH"
    except (AttributeError, TypeError, ValueError):
        pass

    try:
        scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    except (AttributeError, TypeError, ValueError):
        pass

    scene.render.filepath = str(output)

    print(
        f"Video output: {scene.render.filepath}",
        flush=True
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    args = get_args()

    episode_path = Path(args.episode)

    if not episode_path.is_file():
        raise FileNotFoundError(
            f"Episode configuration not found: {episode_path}"
        )

    episode = json.loads(
        episode_path.read_text(encoding="utf-8")
    )

    if not isinstance(episode, dict):
        raise ValueError(
            "episode.json must contain a JSON object."
        )

    if not isinstance(episode.get("scenes"), list):
        raise ValueError(
            "episode.json must contain a 'scenes' list."
        )

    scene = bpy.context.scene

    # Clear the default scene.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # -----------------------------------------------------
    # Materials
    # -----------------------------------------------------

    grass = mat(
        "Savanna grass",
        (0.40, 0.62, 0.22),
        roughness=0.92
    )

    gold = mat(
        "Leo and Gigi gold",
        (1.0, 0.60, 0.13),
        roughness=0.5,
        subsurface=0.035
    )

    mane = mat(
        "Lion mane",
        (0.42, 0.18, 0.06),
        roughness=0.75
    )

    cream = mat(
        "Muzzle cream",
        (1.0, 0.85, 0.59),
        roughness=0.55
    )

    dark = mat(
        "Dark eyes",
        (0.035, 0.025, 0.02),
        roughness=0.3
    )

    grey = mat(
        "Ellie grey",
        (0.48, 0.55, 0.60),
        roughness=0.58,
        subsurface=0.025
    )

    pink = mat(
        "Inner ears",
        (0.9, 0.36, 0.40),
        roughness=0.65
    )

    brown = mat(
        "Spots and tree",
        (0.38, 0.17, 0.06),
        roughness=0.9
    )

    white = mat(
        "Clouds and eye highlights",
        (1.0, 1.0, 1.0),
        roughness=0.7
    )

    caption_material = mat(
        "Caption",
        (0.04, 0.10, 0.07),
        roughness=0.5
    )

    orange = mat(
        "Mango",
        (1.0, 0.30, 0.025),
        roughness=0.45,
        subsurface=0.02
    )

    # -----------------------------------------------------
    # Environment and characters
    # -----------------------------------------------------

    create_environment(
        grass,
        brown,
        white,
        orange
    )

    create_lion(
        gold,
        mane,
        cream,
        dark,
        white
    )

    create_elephant(
        grey,
        pink,
        dark,
        white
    )

    create_giraffe(
        gold,
        brown,
        dark,
        white
    )

    # -----------------------------------------------------
    # Captions
    # -----------------------------------------------------

    captions = []

    for index, item in enumerate(episode["scenes"]):
        obj = label(
            item.get("caption", ""),
            (0, -2.45, 3.35),
            caption_material
        )

        obj.name = f"Caption_{index}"
        captions.append((obj, item))

    # -----------------------------------------------------
    # Camera and lighting
    # -----------------------------------------------------

    camera = create_camera(scene)
    create_lighting()

    # -----------------------------------------------------
    # World and render settings
    # -----------------------------------------------------

    world = bpy.data.worlds.get("World")

    if world is None:
        world = bpy.data.worlds.new("Safari Sky")
        scene.world = world

    scene.world.color = (0.35, 0.52, 0.70)

    world.use_nodes = True

    background = world.node_tree.nodes.get("Background")

    if background:
        background.inputs["Color"].default_value = (
            0.30,
            0.46,
            0.68,
            1.0
        )
        background.inputs["Strength"].default_value = 0.45

    configure_render_engine(scene)

    scene.render.resolution_x = int(
        episode.get("width", 1280)
    )

    scene.render.resolution_y = int(
        episode.get("height", 720)
    )

    # Configurable render resolution.
    scene.render.resolution_percentage = int(
        episode.get("resolution_percentage", 100)
    )

    # Validate resolution percentage.
    scene.render.resolution_percentage = max(
        1,
        min(100, scene.render.resolution_percentage)
    )

    samples = max(
        1,
        int(episode.get("render_samples", 16))
    )

    configure_eevee_samples(scene, samples)

    # Keep the scene optimised without disabling its materials.
    try:
        scene.render.use_simplify = False
    except (AttributeError, TypeError):
        pass

    # High-quality image output.
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False

    # Fixed color-management configuration.
    # This replaces the incompatible hard-coded look assignment.
    configure_color_management(scene)

    # Shadows and ambient occlusion where supported.
    configure_shadow_features(scene)

    # Video timing.
    scene.render.fps = max(
        1,
        int(episode.get("fps", 24))
    )

    scene.frame_start = 1

    duration_seconds = max(
        1,
        int(episode.get("duration_seconds", 32))
    )

    scene.frame_end = duration_seconds * scene.render.fps

    configure_video_output(
        scene,
        args.output
    )

    # -----------------------------------------------------
    # Animation
    # -----------------------------------------------------

    # Characters move throughout the episode.
    animate_character_parts(
        "Leo",
        1,
        scene.frame_end,
        scene.render.fps
    )

    animate_character_parts(
        "Ellie",
        1,
        scene.frame_end,
        scene.render.fps
    )

    animate_character_parts(
        "Gigi",
        1,
        scene.frame_end,
        scene.render.fps
    )

    # Camera movement adds cinematic depth.
    animate_camera(
        camera,
        1,
        scene.frame_end
    )

    # Keep all existing episode captions.
    configure_captions(
        scene,
        captions
    )

    # Set the initial frame explicitly.
    scene.frame_set(scene.frame_start)

    # Render configuration summary for GitHub Actions logs.
    print(
        f"Rendering at {scene.render.resolution_x}x"
        f"{scene.render.resolution_y}, "
        f"{scene.render.resolution_percentage}% scale; "
        f"samples={samples}; "
        f"fps={scene.render.fps}; "
        f"duration={duration_seconds}s; "
        f"frames={scene.frame_end}",
        flush=True
    )

    # Render the animation.
    bpy.ops.render.render(animation=True)

    # Confirm the output file exists after rendering.
    output_file = Path(scene.render.filepath)

    if not output_file.is_file():
        raise RuntimeError(
            "Blender finished rendering, but the expected "
            f"video file was not found: {output_file}"
        )

    if output_file.stat().st_size == 0:
        raise RuntimeError(
            f"Rendered video is empty: {output_file}"
        )

    print(
        f"Render complete: {output_file} "
        f"({output_file.stat().st_size} bytes)",
        flush=True
    )


if __name__ == "__main__":
    main()
