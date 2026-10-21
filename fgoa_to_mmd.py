#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FGO Arcade to MMD Model Converter
=================================
Automated tool to convert FGO Arcade 3D models (weapons & characters)
into fully functional, high-quality MikuMikuDance (.pmx) models.

Features:
- Fixes texture transparency (uninitialized alpha channels).
- Merges separate alpha cutout masks (_a_*.png) into diffuse textures.
- Creates .spa sphere reflection maps for metallic materials.
- Fixes texture paths in PMX (adds missing .png extensions).
- Enables double-sided rendering for cloth, hair, and blades.
- Re-parents disconnected bones (e.g. body_m -> body).
- Adds standard MMD bones: '全ての親' (Master Root) and 'センター' (Center).
- Auto-generates:
  * Stand Version (*_Stand.pmx): Upright on ground (Y=0).
  * Equip Version (*_Equip.pmx): Hand-aligned for Outside Parent (外部親).
  * Physics Version (*_Physics.pmx): Real-time cloth/ribbon simulation (when chains exist).
"""

import os
import sys
import shutil
import math
from PIL import Image

# Ensure tool directory is on import path
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOL_DIR not in sys.path:
    sys.path.insert(0, TOOL_DIR)

from pmx_lib import (
    PMXModel, PMXVertex, PMXMaterial, PMXBone,
    PMXDisplayFrame, PMXDisplayFrameElement,
    PMXRigidBody, PMXJoint
)


def fix_textures_in_folder(folder, log_func=print):
    """
    Fixes texture issues in the given folder:
    1. Alpha channel = 0 bug: converts to solid RGB if no mask exists.
    2. Merges _a_*.png alpha masks into corresponding diffuse textures.
    3. Creates .spa copies of envmap / sphere map textures.
    """
    log_func(f"[*] Checking textures in: {folder}")
    png_files = [f for f in os.listdir(folder) if f.lower().endswith('.png') and not f.startswith('_a_') and not f.startswith('_ramp') and not f.endswith('.bak')]

    for fname in png_files:
        fpath = os.path.join(folder, fname)
        bak_path = os.path.join(folder, fname + '.bak')

        # Check for matching _a_ alpha mask file
        # Format 1: _a_<filename>_a.png (e.g. _a_WP_0022_T01_flag_fur_a.png)
        base_name, _ = os.path.splitext(fname)
        mask_candidates = [
            f"_a_{base_name}_a.png",
            f"_a_{base_name}.png",
            f"{base_name}_a.png",
        ]
        mask_path = None
        for cand in mask_candidates:
            cand_p = os.path.join(folder, cand)
            if os.path.exists(cand_p):
                mask_path = cand_p
                break

        try:
            with Image.open(fpath) as img:
                mode = img.mode
                extrema = img.getextrema()
                has_alpha = 'A' in mode

                # Detect if alpha is completely or almost entirely 0
                alpha_is_broken = False
                if has_alpha:
                    a_min, a_max = extrema[3]
                    if a_max == 0:
                        alpha_is_broken = True

            # Case A: Mask file exists -> merge it into alpha channel
            if mask_path:
                if not os.path.exists(bak_path):
                    shutil.copy2(fpath, bak_path)
                with Image.open(bak_path) as base_img, Image.open(mask_path) as mask_img:
                    rgb = base_img.convert('RGB')
                    mask_l = mask_img.convert('L')
                    if mask_l.size != rgb.size:
                        mask_l = mask_l.resize(rgb.size, Image.Resampling.LANCZOS)
                    merged = Image.merge('RGBA', (*rgb.split(), mask_l))
                    merged.save(fpath, 'PNG')
                log_func(f"  [+] Merged alpha mask: {fname} <- {os.path.basename(mask_path)}")

            # Case B: Alpha channel broken (all zeros) and NO mask -> make solid RGB
            elif alpha_is_broken:
                if not os.path.exists(bak_path):
                    shutil.copy2(fpath, bak_path)
                with Image.open(bak_path) as base_img:
                    solid_rgb = base_img.convert('RGB')
                    solid_rgb.save(fpath, 'PNG')
                log_func(f"  [+] Fixed broken alpha (made solid): {fname}")

        except Exception as e:
            log_func(f"  [!] Texture warning for {fname}: {e}")

    # Create .spa for sphere maps
    for f in os.listdir(folder):
        if 'envmap' in f.lower() and f.lower().endswith('.png'):
            spa_path = os.path.join(folder, os.path.splitext(f)[0] + '.spa')
            if not os.path.exists(spa_path):
                shutil.copy2(os.path.join(folder, f), spa_path)
                log_func(f"  [+] Created sphere map: {os.path.basename(spa_path)}")


def convert_model_pmx(pmx_path, log_func=print):
    """
    Loads, optimizes, and generates ready-to-use MMD models for a given PMX file.
    """
    folder = os.path.dirname(os.path.abspath(pmx_path))
    pmx_file = os.path.basename(pmx_path)
    base_name = os.path.splitext(pmx_file)[0]
    folder_name = os.path.basename(folder)

    log_func(f"\n[*] Processing model: {pmx_file} ({folder_name})")

    # 1. Fix textures in folder first
    fix_textures_in_folder(folder, log_func=log_func)

    # 2. Backup original PMX
    bak_pmx = os.path.join(folder, base_name + '_orig.pmx.bak')
    if not os.path.exists(bak_pmx):
        shutil.copy2(pmx_path, bak_pmx)

    model = PMXModel()
    model.load(bak_pmx)
    log_func(f"  [i] Vertices: {len(model.vertices)}, Materials: {len(model.materials)}, Bones: {len(model.bones)}, Morphs: {len(model.morphs)}")

    # 3. Update textures paths inside PMX
    for i in range(len(model.textures)):
        t = model.textures[i]
        if not t.lower().endswith('.png') and not t.lower().endswith('.spa'):
            # Check if .png exists on disk
            if os.path.exists(os.path.join(folder, t + '.png')):
                model.textures[i] = t + '.png'
            elif os.path.exists(os.path.join(folder, t)):
                model.textures[i] = t
            else:
                model.textures[i] = t + '.png'

    # 4. Enhance Materials: double-sided rendering, ambient
    for mat in model.materials:
        mat.flags = mat.flags | 0x01 # enable double-sided
        # Brighten ambient slightly for MMD default lighting
        mat.ambient = [max(a, 0.55) for a in mat.ambient]
        if any(k in mat.name_jp.lower() for k in ['metal', 'spear', 'blade', 'armor', 'sword', 'gold', 'silver']):
            mat.specular = [0.8, 0.8, 0.8]
            mat.specular_power = 20.0
        else:
            mat.specular = [0.2, 0.2, 0.2]
            mat.specular_power = 5.0

    # 5. Detect if weapon / prop
    is_weapon = len(model.morphs) == 0 and any(k in folder.lower() or k in pmx_file.lower() for k in ['wp', 'weapon', 'sword', 'flag', 'spear', 'bow', 'shield'])
    if not is_weapon and len(model.bones) <= 50:
        is_weapon = True

    if is_weapon:
        log_func(f"  [i] Detected as Weapon / Prop model.")
        _convert_weapon(model, folder, folder_name, base_name, pmx_path, log_func)
    else:
        log_func(f"  [i] Detected as Character / SVT model.")
        _convert_character(model, folder, folder_name, base_name, pmx_path, log_func)


def _convert_weapon(raw_model, folder, folder_name, base_name, original_pmx_path, log_func):
    """Handles weapon-specific rigging, orientation, and physics."""
    # Find disconnected child root bones (like body_m)
    body_idx = -1
    for i, b in enumerate(raw_model.bones):
        if b.name_jp.lower() == 'body':
            body_idx = i
            break

    # If body_m is parent -1, connect it to body
    if body_idx >= 0:
        for i, b in enumerate(raw_model.bones):
            if b.name_jp.lower() in ['body_m', 'cloth_root', 'flag_root'] and b.parent_index == -1:
                b.parent_index = body_idx
                log_func(f"  [+] Connected bone '{b.name_jp}' to '{raw_model.bones[body_idx].name_jp}' (parent_index={body_idx})")

    # Friendly bone renaming map
    rename_map = {
        'wrist_l': ('持ち手', 'Grip'),
        'wrist_r': ('持ち手', 'Grip'),
        'body': ('本体', 'Body'),
        'body_m': ('装飾元', 'Cloth_Root'),
    }

    # ----------------------------------------------------
    # Model 1: Equip Version (Original Hand-Local Coordinates)
    # ----------------------------------------------------
    equip = PMXModel()
    equip.load(original_pmx_path if os.path.exists(original_pmx_path) else os.path.join(folder, base_name + '_orig.pmx.bak'))
    # Re-apply texture and material fixes
    equip.textures = list(raw_model.textures)
    equip.materials = raw_model.materials

    # Insert 全ての親 at index 0
    root_bone = PMXBone()
    root_bone.name_jp = "全ての親"
    root_bone.name_en = "Mother"
    root_bone.pos = [0.0, 0.0, 0.0]
    root_bone.parent_index = -1
    root_bone.flags = 0x0002 | 0x0004 | 0x0008 | 0x0010
    root_bone.tail_pos = [0.0, 0.0, 0.2]

    # Shift vertex weights
    for v in equip.vertices:
        if v.weight_type == 0: v.bones[0] += 1
        elif v.weight_type in (1, 3):
            v.bones[0] += 1; v.bones[1] += 1
        elif v.weight_type in (2, 4):
            for bi in range(4): v.bones[bi] += 1

    old_bones = equip.bones
    for b in old_bones:
        if b.parent_index == -1:
            b.parent_index = 0
        else:
            b.parent_index += 1
        if b.tail_is_bone:
            b.tail_bone_index += 1

    # Connect body_m (old index 2 -> new 3) to body (old index 1 -> new 2) if present
    for i, b in enumerate(old_bones):
        if b.name_jp.lower() == 'body_m' and body_idx >= 0:
            b.parent_index = body_idx + 1

    for b in old_bones:
        if b.name_jp.lower() in rename_map:
            b.name_jp, b.name_en = rename_map[b.name_jp.lower()]

    equip.bones = [root_bone] + old_bones

    # Display Frames
    df_root = PMXDisplayFrame()
    df_root.name_jp = "Root"; df_root.name_en = "Root"; df_root.special = 1
    df_root.elements.append(PMXDisplayFrameElement(0, 0))

    df_main = PMXDisplayFrame()
    df_main.name_jp = "メイン"; df_main.name_en = "Main"; df_main.special = 0
    for i in range(1, min(5, len(equip.bones))):
        df_main.elements.append(PMXDisplayFrameElement(0, i))

    df_other = PMXDisplayFrame()
    df_other.name_jp = "その他"; df_other.name_en = "Other"; df_other.special = 0
    for i in range(5, len(equip.bones)):
        df_other.elements.append(PMXDisplayFrameElement(0, i))

    equip.display_frames = [df_root, df_main]
    if df_other.elements:
        equip.display_frames.append(df_other)

    equip_out = os.path.join(folder, f"{folder_name}_Equip.pmx")
    equip.save(equip_out)
    log_func(f"  [+] Created Equip Model: {os.path.basename(equip_out)}")

    # ----------------------------------------------------
    # Model 2: Stand / Upright Version (Rotated to Stand on Ground)
    # ----------------------------------------------------
    stand = PMXModel()
    stand.load(original_pmx_path if os.path.exists(original_pmx_path) else os.path.join(folder, base_name + '_orig.pmx.bak'))
    stand.textures = list(raw_model.textures)
    stand.materials = raw_model.materials

    # Check orientation: is shaft along Z?
    zs = [v.pos[2] for v in stand.vertices]
    ys = [v.pos[1] for v in stand.vertices]
    z_span = max(zs) - min(zs)
    y_span = max(ys) - min(ys)
    min_z = min(zs)

    needs_rotation = z_span > y_span * 2.0
    z_offset = -min_z if needs_rotation else 0.0

    def rot_pos(p):
        if needs_rotation:
            return [p[0], p[2] + z_offset, -p[1]]
        return list(p)

    def rot_vec(v):
        if needs_rotation:
            return [v[0], v[2], -v[1]]
        return list(v)

    for v in stand.vertices:
        v.pos = rot_pos(v.pos)
        v.normal = rot_vec(v.normal)
        if v.weight_type == 3:
            v.sdef_c = rot_pos(v.sdef_c)
            v.sdef_r0 = rot_vec(v.sdef_r0)
            v.sdef_r1 = rot_vec(v.sdef_r1)

    # Shift vertex weights for 2 inserted root bones (全ての親 + センター)
    for v in stand.vertices:
        if v.weight_type == 0: v.bones[0] += 2
        elif v.weight_type in (1, 3):
            v.bones[0] += 2; v.bones[1] += 2
        elif v.weight_type in (2, 4):
            for bi in range(4): v.bones[bi] += 2

    s_bones = stand.bones
    for b in s_bones:
        b.pos = rot_pos(b.pos)
        if b.tail_is_bone:
            b.tail_bone_index += 2
        else:
            b.tail_pos = rot_vec(b.tail_pos)
        if b.flags & 0x0400: b.fixed_axis = rot_vec(b.fixed_axis)
        if b.flags & 0x0800:
            b.local_x = rot_vec(b.local_x)
            b.local_z = rot_vec(b.local_z)
        if b.parent_index == -1:
            b.parent_index = 1 # parent to センター
        else:
            b.parent_index += 2

    # Connect body_m if present
    for i, b in enumerate(s_bones):
        if b.name_jp.lower() == 'body_m' and body_idx >= 0:
            b.parent_index = body_idx + 2

    for b in s_bones:
        if b.name_jp.lower() in rename_map:
            b.name_jp, b.name_en = rename_map[b.name_jp.lower()]

    # Insert 全ての親 and センター
    b_mother = PMXBone()
    b_mother.name_jp = "全ての親"; b_mother.name_en = "Mother"
    b_mother.pos = [0.0, 0.0, 0.0]; b_mother.parent_index = -1
    b_mother.flags = 0x0002 | 0x0004 | 0x0008 | 0x0010
    b_mother.tail_pos = [0.0, 0.2, 0.0]

    b_center = PMXBone()
    b_center.name_jp = "センター"; b_center.name_en = "Center"
    b_center.pos = [0.0, 0.0, 0.0]; b_center.parent_index = 0
    b_center.flags = 0x0002 | 0x0004 | 0x0008 | 0x0010
    b_center.tail_pos = [0.0, 0.2, 0.0]

    stand.bones = [b_mother, b_center] + s_bones

    df_root = PMXDisplayFrame()
    df_root.name_jp = "Root"; df_root.name_en = "Root"; df_root.special = 1
    df_root.elements.append(PMXDisplayFrameElement(0, 0))

    df_center = PMXDisplayFrame()
    df_center.name_jp = "センター"; df_center.name_en = "Center"; df_center.special = 0
    df_center.elements.append(PMXDisplayFrameElement(0, 1))
    for i in range(2, min(6, len(stand.bones))):
        df_center.elements.append(PMXDisplayFrameElement(0, i))

    df_other = PMXDisplayFrame()
    df_other.name_jp = "パーツ"; df_other.name_en = "Parts"; df_other.special = 0
    for i in range(6, len(stand.bones)):
        df_other.elements.append(PMXDisplayFrameElement(0, i))

    stand.display_frames = [df_root, df_center]
    if df_other.elements:
        stand.display_frames.append(df_other)

    stand_out = os.path.join(folder, f"{folder_name}_Stand.pmx")
    stand.save(stand_out)
    log_func(f"  [+] Created Stand Model: {os.path.basename(stand_out)}")

    # Also update original PMX in-place
    stand.save(original_pmx_path)
    log_func(f"  [+] Updated original {os.path.basename(original_pmx_path)} in place.")

    # ----------------------------------------------------
    # Model 3: Physics Version (If multiple cloth/chain bones exist)
    # ----------------------------------------------------
    if len(stand.bones) >= 15:
        log_func("  [*] Generating Physics Rigid Bodies & Joints for cloth chains...")
        phys = PMXModel()
        phys.load(stand_out)

        rigid_bodies = []
        joints = []

        # Find chain bones (parent-child chains with > 2 segments)
        children_map = {}
        for idx, b in enumerate(phys.bones):
            children_map.setdefault(b.parent_index, []).append(idx)

        # Trace chains
        chains = []
        visited = set()
        for root_b in children_map.get(4, []) + children_map.get(3, []) + children_map.get(2, []):
            chain = [root_b]
            cur = root_b
            while cur in children_map and len(children_map[cur]) == 1:
                nxt = children_map[cur][0]
                chain.append(nxt)
                cur = nxt
            if len(chain) >= 2:
                chains.append(chain)
                for ci in chain: visited.add(ci)

        if chains:
            # Rigid body for handle
            rb_handle = PMXRigidBody()
            rb_handle.name_jp = "剛体_本体"; rb_handle.name_en = "RB_Body"
            rb_handle.bone_index = 2
            rb_handle.group = 0; rb_handle.non_collision_group_mask = 0xFFFF
            rb_handle.shape_type = 2; rb_handle.size = [0.05, 1.5, 0.0]
            rb_handle.pos = list(phys.bones[2].pos); rb_handle.physics_type = 0
            rigid_bodies.append(rb_handle)

            for c_i, chain in enumerate(chains):
                prev_rb = -1
                for step, b_idx in enumerate(chain):
                    bone = phys.bones[b_idx]
                    rb = PMXRigidBody()
                    rb.name_jp = f"剛体_装飾_{c_i}_{step}"
                    rb.name_en = f"RB_Part_{c_i}_{step}"
                    rb.bone_index = b_idx
                    rb.group = 1
                    rb.non_collision_group_mask = (1 << 0) | (1 << 1)
                    rb.shape_type = 0
                    rb.size = [0.12, 0.0, 0.0]
                    rb.pos = list(bone.pos)
                    rb.mass = 0.5
                    rb.linear_damping = 0.4; rb.angular_damping = 0.6
                    rb.physics_type = 0 if step == 0 else 1 # dynamic after root
                    rb_idx = len(rigid_bodies)
                    rigid_bodies.append(rb)

                    if prev_rb >= 0:
                        jt = PMXJoint()
                        jt.name_jp = f"関節_{c_i}_{step}"
                        jt.name_en = f"Joint_{c_i}_{step}"
                        jt.rigid_body_a = prev_rb
                        jt.rigid_body_b = rb_idx
                        jt.pos = list(bone.pos)
                        jt.pos_min = [-0.01, -0.01, -0.01]; jt.pos_max = [0.01, 0.01, 0.01]
                        jt.rot_min = [-math.radians(45), -math.radians(45), -math.radians(45)]
                        jt.rot_max = [math.radians(45), math.radians(45), math.radians(45)]
                        jt.pos_spring = [100.0, 100.0, 100.0]
                        jt.rot_spring = [20.0, 20.0, 20.0]
                        joints.append(jt)

                    prev_rb = rb_idx

            phys.rigid_bodies = rigid_bodies
            phys.joints = joints
            phys_out = os.path.join(folder, f"{folder_name}_Physics.pmx")
            phys.save(phys_out)
            log_func(f"  [+] Created Physics Model: {os.path.basename(phys_out)} ({len(rigid_bodies)} RBs, {len(joints)} Joints)")


def _convert_character(model, folder, folder_name, base_name, original_pmx_path, log_func):
    """Handles character model adjustments."""
    # Ensure 全ての親 exists
    has_mother = any(b.name_jp == '全ての親' for b in model.bones)
    if not has_mother:
        root_bone = PMXBone()
        root_bone.name_jp = "全ての親"; root_bone.name_en = "Mother"
        root_bone.pos = [0.0, 0.0, 0.0]; root_bone.parent_index = -1
        root_bone.flags = 0x0002 | 0x0004 | 0x0008 | 0x0010
        root_bone.tail_pos = [0.0, 0.2, 0.0]

        # Shift vertex weights
        for v in model.vertices:
            if v.weight_type == 0: v.bones[0] += 1
            elif v.weight_type in (1, 3):
                v.bones[0] += 1; v.bones[1] += 1
            elif v.weight_type in (2, 4):
                for bi in range(4): v.bones[bi] += 1

        for b in model.bones:
            if b.parent_index == -1: b.parent_index = 0
            else: b.parent_index += 1
            if b.tail_is_bone: b.tail_bone_index += 1

        model.bones = [root_bone] + model.bones
        log_func("  [+] Added '全ての親' master root bone to character.")

    char_out = os.path.join(folder, f"{folder_name}_MMD.pmx")
    model.save(char_out)
    log_func(f"  [+] Created Character MMD Model: {os.path.basename(char_out)}")
    model.save(original_pmx_path)
    log_func(f"  [+] Updated original {os.path.basename(original_pmx_path)} in place.")


def process_target(target_path, log_func=print):
    """Processes a folder, a PMX file, or recursively scans if target is a root directory."""
    target_path = os.path.abspath(target_path)
    if not os.path.exists(target_path):
        log_func(f"[!] Path not found: {target_path}")
        return

    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pmx') and not target_path.lower().endswith('.bak'):
            convert_model_pmx(target_path, log_func=log_func)
        else:
            log_func(f"[!] Target is not a PMX file: {target_path}")
        return

    # If it's a directory:
    # 1. Check if there are PMX files directly in this directory
    direct_pmxs = [f for f in os.listdir(target_path) if f.lower().endswith('.pmx') and not f.lower().endswith('.bak')]
    if direct_pmxs:
        for pmx in direct_pmxs:
            convert_model_pmx(os.path.join(target_path, pmx), log_func=log_func)
    else:
        # Recursive scan
        found_any = False
        for root, dirs, files in os.walk(target_path):
            pmxs = [f for f in files if f.lower().endswith('.pmx') and not f.lower().endswith('.bak') and '_orig' not in f.lower() and not f.endswith('_Equip.pmx') and not f.endswith('_Stand.pmx') and not f.endswith('_Physics.pmx') and not f.endswith('_MMD.pmx')]
            for pmx in pmxs:
                found_any = True
                convert_model_pmx(os.path.join(root, pmx), log_func=log_func)
        if not found_any:
            log_func(f"[!] No unconverted PMX models found in: {target_path}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fgoa_to_mmd.py <folder_or_pmx_file>")
        print("  python fgoa_to_mmd.py --all <root_folder>")
        print()
        path = input("Masukkan path folder atau file PMX (atau tekan Enter untuk E:\\FGO\\FGOA): ").strip('\"\' ')
        if not path:
            path = r"E:\FGO\FGOA"
        process_target(path)
    else:
        if sys.argv[1] == '--all':
            root = sys.argv[2] if len(sys.argv) > 2 else r"E:\FGO\FGOA"
            process_target(root)
        else:
            process_target(sys.argv[1])
