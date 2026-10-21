import struct
import os

class PMXVertex:
    def __init__(self):
        self.pos = [0.0, 0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.uv = [0.0, 0.0]
        self.extra_uv = []
        self.weight_type = 0
        self.bones = [0, 0, 0, 0]
        self.weights = [0.0, 0.0, 0.0, 0.0]
        self.sdef_c = [0.0, 0.0, 0.0]
        self.sdef_r0 = [0.0, 0.0, 0.0]
        self.sdef_r1 = [0.0, 0.0, 0.0]
        self.edge_scale = 1.0

class PMXMaterial:
    def __init__(self):
        self.name_jp = ""
        self.name_en = ""
        self.diffuse = [1.0, 1.0, 1.0, 1.0]
        self.specular = [0.0, 0.0, 0.0]
        self.specular_power = 5.0
        self.ambient = [0.55, 0.55, 0.55]
        self.flags = 0x0F # double-sided, shadows
        self.edge_color = [0.0, 0.0, 0.0, 1.0]
        self.edge_size = 0.0
        self.diffuse_texture_index = -1
        self.sphere_texture_index = -1
        self.sphere_mode = 0
        self.toon_flag = 1
        self.toon_index = 0
        self.memo = ""
        self.indices_count = 0

class PMXBone:
    def __init__(self):
        self.name_jp = ""
        self.name_en = ""
        self.pos = [0.0, 0.0, 0.0]
        self.parent_index = -1
        self.transform_level = 0
        self.flags = 0x0002 | 0x0008 | 0x0010
        self.tail_is_bone = False
        self.tail_bone_index = -1
        self.tail_pos = [0.0, 0.0, 0.0]
        self.inherit_parent_index = -1
        self.inherit_weight = 0.0
        self.fixed_axis = [0.0, 0.0, 0.0]
        self.local_x = [1.0, 0.0, 0.0]
        self.local_z = [0.0, 0.0, 1.0]
        self.external_parent_key = 0
        self.ik_target = -1
        self.ik_iterations = 0
        self.ik_angle_limit = 0.0
        self.ik_links = []

class PMXMorph:
    def __init__(self):
        self.name_jp = ""
        self.name_en = ""
        self.panel = 4
        self.morph_type = 1
        self.item_count = 0
        self.raw_items_data = b""

class PMXDisplayFrameElement:
    def __init__(self, target_type=0, index=0):
        self.type = target_type
        self.index = index

class PMXDisplayFrame:
    def __init__(self):
        self.name_jp = ""
        self.name_en = ""
        self.special = 0
        self.elements = []

class PMXRigidBody:
    def __init__(self):
        self.name_jp = ""
        self.name_en = ""
        self.bone_index = -1
        self.group = 0
        self.non_collision_group_mask = 0
        self.shape_type = 0
        self.size = [1.0, 1.0, 1.0]
        self.pos = [0.0, 0.0, 0.0]
        self.rot = [0.0, 0.0, 0.0]
        self.mass = 1.0
        self.linear_damping = 0.5
        self.angular_damping = 0.5
        self.restitution = 0.0
        self.friction = 0.5
        self.physics_type = 0

class PMXJoint:
    def __init__(self):
        self.name_jp = ""
        self.name_en = ""
        self.type = 0
        self.rigid_body_a = -1
        self.rigid_body_b = -1
        self.pos = [0.0, 0.0, 0.0]
        self.rot = [0.0, 0.0, 0.0]
        self.pos_min = [0.0, 0.0, 0.0]
        self.pos_max = [0.0, 0.0, 0.0]
        self.rot_min = [0.0, 0.0, 0.0]
        self.rot_max = [0.0, 0.0, 0.0]
        self.pos_spring = [0.0, 0.0, 0.0]
        self.rot_spring = [0.0, 0.0, 0.0]

class PMXModel:
    def __init__(self):
        self.version = 2.0
        self.encoding = "utf-16-le"
        self.name_jp = ""
        self.name_en = ""
        self.comment_jp = ""
        self.comment_en = ""
        self.vertices = []
        self.indices = []
        self.textures = []
        self.materials = []
        self.bones = []
        self.morphs = []
        self.display_frames = []
        self.rigid_bodies = []
        self.joints = []

    def load(self, path):
        with open(path, 'rb') as f:
            magic = f.read(4)
            if magic != b'PMX ':
                raise ValueError("Not a valid PMX file")
            self.version = struct.unpack('<f', f.read(4))[0]
            info_len = ord(f.read(1))
            info = f.read(info_len)
            self.encoding = 'utf-16-le' if info[0] == 0 else 'utf-8'
            extra_uv = info[1]
            v_size = info[2]
            t_size = info[3]
            m_size = info[4]
            b_size = info[5]
            morph_size = info[6]
            rb_size = info[7]

            def read_str():
                l = struct.unpack('<i', f.read(4))[0]
                return f.read(l).decode(self.encoding, errors='replace')

            def read_idx(size, signed=False):
                if size == 1: return struct.unpack('<b' if signed else '<B', f.read(1))[0]
                elif size == 2: return struct.unpack('<h' if signed else '<H', f.read(2))[0]
                elif size == 4: return struct.unpack('<i' if signed else '<I', f.read(4))[0]

            self.name_jp = read_str()
            self.name_en = read_str()
            self.comment_jp = read_str()
            self.comment_en = read_str()

            # Vertices
            num_verts = struct.unpack('<i', f.read(4))[0]
            self.vertices = []
            for _ in range(num_verts):
                v = PMXVertex()
                v.pos = list(struct.unpack('<3f', f.read(12)))
                v.normal = list(struct.unpack('<3f', f.read(12)))
                v.uv = list(struct.unpack('<2f', f.read(8)))
                v.extra_uv = [list(struct.unpack('<4f', f.read(16))) for _ in range(extra_uv)]
                v.weight_type = ord(f.read(1))
                if v.weight_type == 0:
                    v.bones[0] = read_idx(b_size)
                    v.weights[0] = 1.0
                elif v.weight_type == 1:
                    v.bones[0] = read_idx(b_size)
                    v.bones[1] = read_idx(b_size)
                    v.weights[0] = struct.unpack('<f', f.read(4))[0]
                    v.weights[1] = 1.0 - v.weights[0]
                elif v.weight_type in (2, 4):
                    for bi in range(4): v.bones[bi] = read_idx(b_size)
                    v.weights = list(struct.unpack('<4f', f.read(16)))
                elif v.weight_type == 3:
                    v.bones[0] = read_idx(b_size)
                    v.bones[1] = read_idx(b_size)
                    v.weights[0] = struct.unpack('<f', f.read(4))[0]
                    v.weights[1] = 1.0 - v.weights[0]
                    v.sdef_c = list(struct.unpack('<3f', f.read(12)))
                    v.sdef_r0 = list(struct.unpack('<3f', f.read(12)))
                    v.sdef_r1 = list(struct.unpack('<3f', f.read(12)))
                v.edge_scale = struct.unpack('<f', f.read(4))[0]
                self.vertices.append(v)

            # Indices
            num_indices = struct.unpack('<i', f.read(4))[0]
            self.indices = [read_idx(v_size) for _ in range(num_indices)]

            # Textures
            num_textures = struct.unpack('<i', f.read(4))[0]
            self.textures = [read_str() for _ in range(num_textures)]

            # Materials
            num_materials = struct.unpack('<i', f.read(4))[0]
            self.materials = []
            for _ in range(num_materials):
                m = PMXMaterial()
                m.name_jp = read_str()
                m.name_en = read_str()
                m.diffuse = list(struct.unpack('<4f', f.read(16)))
                m.specular = list(struct.unpack('<3f', f.read(12)))
                m.specular_power = struct.unpack('<f', f.read(4))[0]
                m.ambient = list(struct.unpack('<3f', f.read(12)))
                m.flags = ord(f.read(1))
                m.edge_color = list(struct.unpack('<4f', f.read(16)))
                m.edge_size = struct.unpack('<f', f.read(4))[0]
                m.diffuse_texture_index = read_idx(t_size, True)
                m.sphere_texture_index = read_idx(t_size, True)
                m.sphere_mode = ord(f.read(1))
                m.toon_flag = ord(f.read(1))
                if m.toon_flag == 0:
                    m.toon_index = read_idx(t_size, True)
                else:
                    m.toon_index = ord(f.read(1))
                m.memo = read_str()
                m.indices_count = struct.unpack('<i', f.read(4))[0]
                self.materials.append(m)

            # Bones
            num_bones = struct.unpack('<i', f.read(4))[0]
            self.bones = []
            for _ in range(num_bones):
                b = PMXBone()
                b.name_jp = read_str()
                b.name_en = read_str()
                b.pos = list(struct.unpack('<3f', f.read(12)))
                b.parent_index = read_idx(b_size, True)
                b.transform_level = struct.unpack('<i', f.read(4))[0]
                b.flags = struct.unpack('<H', f.read(2))[0]
                if b.flags & 0x0001:
                    b.tail_is_bone = True
                    b.tail_bone_index = read_idx(b_size, True)
                else:
                    b.tail_is_bone = False
                    b.tail_pos = list(struct.unpack('<3f', f.read(12)))
                if b.flags & 0x0100:
                    b.inherit_parent_index = read_idx(b_size, True)
                    b.inherit_weight = struct.unpack('<f', f.read(4))[0]
                if b.flags & 0x0200:
                    b.inherit_parent_index = read_idx(b_size, True)
                    b.inherit_weight = struct.unpack('<f', f.read(4))[0]
                if b.flags & 0x0400:
                    b.fixed_axis = list(struct.unpack('<3f', f.read(12)))
                if b.flags & 0x0800:
                    b.local_x = list(struct.unpack('<3f', f.read(12)))
                    b.local_z = list(struct.unpack('<3f', f.read(12)))
                if b.flags & 0x2000:
                    b.external_parent_key = struct.unpack('<i', f.read(4))[0]
                if b.flags & 0x0020:
                    b.ik_target = read_idx(b_size, True)
                    b.ik_iterations = struct.unpack('<i', f.read(4))[0]
                    b.ik_angle_limit = struct.unpack('<f', f.read(4))[0]
                    nl = struct.unpack('<i', f.read(4))[0]
                    b.ik_links = []
                    for _ in range(nl):
                        lb = read_idx(b_size, True)
                        hl = ord(f.read(1))
                        lim = None
                        if hl:
                            lim = (list(struct.unpack('<3f', f.read(12))), list(struct.unpack('<3f', f.read(12))))
                        b.ik_links.append((lb, lim))
                self.bones.append(b)

            # Morphs
            num_morphs = struct.unpack('<i', f.read(4))[0]
            self.morphs = []
            for _ in range(num_morphs):
                morph = PMXMorph()
                morph.name_jp = read_str()
                morph.name_en = read_str()
                morph.panel = ord(f.read(1))
                morph.morph_type = ord(f.read(1))
                item_cnt = struct.unpack('<i', f.read(4))[0]
                # Sega arcade dump stores vertex morph item as: 4-byte vertex index + 12-byte vec3 pos = 16 bytes
                mt = morph.morph_type
                if mt == 0: item_len = morph_size + 4
                elif mt == 1: item_len = 16 # 4 bytes v_idx + 12 bytes offset
                elif mt == 2: item_len = b_size + 28
                elif mt in (3, 4, 5, 6, 7): item_len = 20 # 4 bytes v_idx + 16 bytes uv
                elif mt == 8: item_len = m_size + 113
                elif mt == 9: item_len = morph_size + 4
                elif mt == 10: item_len = rb_size + 25
                else: item_len = 0

                morph.raw_items_data = f.read(item_cnt * item_len)
                morph.item_count = item_cnt
                self.morphs.append(morph)

            # Display Frames
            num_frames = struct.unpack('<i', f.read(4))[0]
            self.display_frames = []
            for _ in range(num_frames):
                df = PMXDisplayFrame()
                df.name_jp = read_str()
                df.name_en = read_str()
                df.special = ord(f.read(1))
                elem_cnt = struct.unpack('<i', f.read(4))[0]
                for _ in range(elem_cnt):
                    t = ord(f.read(1))
                    idx = read_idx(b_size if t == 0 else morph_size)
                    df.elements.append(PMXDisplayFrameElement(t, idx))
                self.display_frames.append(df)

            # Rigid bodies
            num_rb = struct.unpack('<i', f.read(4))[0]
            self.rigid_bodies = []
            for _ in range(num_rb):
                rb = PMXRigidBody()
                rb.name_jp = read_str()
                rb.name_en = read_str()
                rb.bone_index = read_idx(b_size, True)
                rb.group = ord(f.read(1))
                rb.non_collision_group_mask = struct.unpack('<H', f.read(2))[0]
                rb.shape_type = ord(f.read(1))
                rb.size = list(struct.unpack('<3f', f.read(12)))
                rb.pos = list(struct.unpack('<3f', f.read(12)))
                rb.rot = list(struct.unpack('<3f', f.read(12)))
                rb.mass = struct.unpack('<f', f.read(4))[0]
                rb.linear_damping = struct.unpack('<f', f.read(4))[0]
                rb.angular_damping = struct.unpack('<f', f.read(4))[0]
                rb.restitution = struct.unpack('<f', f.read(4))[0]
                rb.friction = struct.unpack('<f', f.read(4))[0]
                rb.physics_type = ord(f.read(1))
                self.rigid_bodies.append(rb)

            # Joints
            num_joints = struct.unpack('<i', f.read(4))[0]
            self.joints = []
            for _ in range(num_joints):
                j = PMXJoint()
                j.name_jp = read_str()
                j.name_en = read_str()
                j.type = ord(f.read(1))
                j.rigid_body_a = read_idx(rb_size, True)
                j.rigid_body_b = read_idx(rb_size, True)
                j.pos = list(struct.unpack('<3f', f.read(12)))
                j.rot = list(struct.unpack('<3f', f.read(12)))
                j.pos_min = list(struct.unpack('<3f', f.read(12)))
                j.pos_max = list(struct.unpack('<3f', f.read(12)))
                j.rot_min = list(struct.unpack('<3f', f.read(12)))
                j.rot_max = list(struct.unpack('<3f', f.read(12)))
                j.pos_spring = list(struct.unpack('<3f', f.read(12)))
                j.rot_spring = list(struct.unpack('<3f', f.read(12)))
                self.joints.append(j)

    def save(self, path):
        v_size = 1 if len(self.vertices) < 128 else (2 if len(self.vertices) < 32768 else 4)
        t_size = 1 if len(self.textures) < 128 else (2 if len(self.textures) < 32768 else 4)
        m_size = 1 if len(self.materials) < 128 else (2 if len(self.materials) < 32768 else 4)
        b_size = 1 if len(self.bones) < 128 else (2 if len(self.bones) < 32768 else 4)
        morph_size = 1 if len(self.morphs) < 128 else (2 if len(self.morphs) < 32768 else 4)
        rb_size = 1 if len(self.rigid_bodies) < 128 else (2 if len(self.rigid_bodies) < 32768 else 4)

        extra_uv = 0
        if self.vertices and self.vertices[0].extra_uv:
            extra_uv = len(self.vertices[0].extra_uv)

        enc_flag = 0 if self.encoding == 'utf-16-le' else 1

        def pack_str(s):
            b = s.encode(self.encoding)
            return struct.pack('<i', len(b)) + b

        def pack_idx(val, size, signed=False):
            if size == 1: return struct.pack('<b' if signed else '<B', val)
            elif size == 2: return struct.pack('<h' if signed else '<H', val)
            elif size == 4: return struct.pack('<i' if signed else '<I', val)

        with open(path, 'wb') as f:
            f.write(b'PMX ')
            f.write(struct.pack('<f', 2.0))
            f.write(struct.pack('<B', 8))
            f.write(bytes([enc_flag, extra_uv, v_size, t_size, m_size, b_size, morph_size, rb_size]))

            f.write(pack_str(self.name_jp))
            f.write(pack_str(self.name_en))
            f.write(pack_str(self.comment_jp))
            f.write(pack_str(self.comment_en))

            # Vertices
            f.write(struct.pack('<i', len(self.vertices)))
            for v in self.vertices:
                f.write(struct.pack('<3f', *v.pos))
                f.write(struct.pack('<3f', *v.normal))
                f.write(struct.pack('<2f', *v.uv))
                for eu in v.extra_uv:
                    f.write(struct.pack('<4f', *eu))
                f.write(struct.pack('<B', v.weight_type))
                if v.weight_type == 0:
                    f.write(pack_idx(v.bones[0], b_size))
                elif v.weight_type == 1:
                    f.write(pack_idx(v.bones[0], b_size))
                    f.write(pack_idx(v.bones[1], b_size))
                    f.write(struct.pack('<f', v.weights[0]))
                elif v.weight_type in (2, 4):
                    for bi in range(4): f.write(pack_idx(v.bones[bi], b_size))
                    f.write(struct.pack('<4f', *v.weights))
                elif v.weight_type == 3:
                    f.write(pack_idx(v.bones[0], b_size))
                    f.write(pack_idx(v.bones[1], b_size))
                    f.write(struct.pack('<f', v.weights[0]))
                    f.write(struct.pack('<3f', *v.sdef_c))
                    f.write(struct.pack('<3f', *v.sdef_r0))
                    f.write(struct.pack('<3f', *v.sdef_r1))
                f.write(struct.pack('<f', v.edge_scale))

            # Indices
            f.write(struct.pack('<i', len(self.indices)))
            for idx in self.indices:
                f.write(pack_idx(idx, v_size))

            # Textures
            f.write(struct.pack('<i', len(self.textures)))
            for t in self.textures:
                f.write(pack_str(t))

            # Materials
            f.write(struct.pack('<i', len(self.materials)))
            for m in self.materials:
                f.write(pack_str(m.name_jp))
                f.write(pack_str(m.name_en))
                f.write(struct.pack('<4f', *m.diffuse))
                f.write(struct.pack('<3f', *m.specular))
                f.write(struct.pack('<f', m.specular_power))
                f.write(struct.pack('<3f', *m.ambient))
                f.write(struct.pack('<B', m.flags))
                f.write(struct.pack('<4f', *m.edge_color))
                f.write(struct.pack('<f', m.edge_size))
                f.write(pack_idx(m.diffuse_texture_index, t_size, True))
                f.write(pack_idx(m.sphere_texture_index, t_size, True))
                f.write(struct.pack('<B', m.sphere_mode))
                f.write(struct.pack('<B', m.toon_flag))
                if m.toon_flag == 0:
                    f.write(pack_idx(m.toon_index, t_size, True))
                else:
                    f.write(struct.pack('<B', m.toon_index))
                f.write(pack_str(m.memo))
                f.write(struct.pack('<i', m.indices_count))

            # Bones
            f.write(struct.pack('<i', len(self.bones)))
            for b in self.bones:
                f.write(pack_str(b.name_jp))
                f.write(pack_str(b.name_en))
                f.write(struct.pack('<3f', *b.pos))
                f.write(pack_idx(b.parent_index, b_size, True))
                f.write(struct.pack('<i', b.transform_level))
                f.write(struct.pack('<H', b.flags))
                if b.flags & 0x0001:
                    f.write(pack_idx(b.tail_bone_index, b_size, True))
                else:
                    f.write(struct.pack('<3f', *b.tail_pos))
                if b.flags & 0x0100:
                    f.write(pack_idx(b.inherit_parent_index, b_size, True))
                    f.write(struct.pack('<f', b.inherit_weight))
                if b.flags & 0x0200:
                    f.write(pack_idx(b.inherit_parent_index, b_size, True))
                    f.write(struct.pack('<f', b.inherit_weight))
                if b.flags & 0x0400:
                    f.write(struct.pack('<3f', *b.fixed_axis))
                if b.flags & 0x0800:
                    f.write(struct.pack('<3f', *b.local_x))
                    f.write(struct.pack('<3f', *b.local_z))
                if b.flags & 0x2000:
                    f.write(struct.pack('<i', b.external_parent_key))
                if b.flags & 0x0020:
                    f.write(pack_idx(b.ik_target, b_size, True))
                    f.write(struct.pack('<i', b.ik_iterations))
                    f.write(struct.pack('<f', b.ik_angle_limit))
                    f.write(struct.pack('<i', len(b.ik_links)))
                    for lb, lim in b.ik_links:
                        f.write(pack_idx(lb, b_size, True))
                        if lim is not None:
                            f.write(b'\x01')
                            f.write(struct.pack('<3f', *lim[0]))
                            f.write(struct.pack('<3f', *lim[1]))
                        else:
                            f.write(b'\x00')

            # Morphs
            f.write(struct.pack('<i', len(self.morphs)))
            for morph in self.morphs:
                f.write(pack_str(morph.name_jp))
                f.write(pack_str(morph.name_en))
                f.write(struct.pack('<B', morph.panel))
                f.write(struct.pack('<B', morph.morph_type))
                f.write(struct.pack('<i', morph.item_count))
                f.write(morph.raw_items_data)

            # Display Frames
            f.write(struct.pack('<i', len(self.display_frames)))
            for df in self.display_frames:
                f.write(pack_str(df.name_jp))
                f.write(pack_str(df.name_en))
                f.write(struct.pack('<B', df.special))
                f.write(struct.pack('<i', len(df.elements)))
                for elem in df.elements:
                    f.write(struct.pack('<B', elem.type))
                    if elem.type == 0:
                        f.write(pack_idx(elem.index, b_size))
                    else:
                        f.write(pack_idx(elem.index, morph_size))

            # Rigid Bodies
            f.write(struct.pack('<i', len(self.rigid_bodies)))
            for rb in self.rigid_bodies:
                f.write(pack_str(rb.name_jp))
                f.write(pack_str(rb.name_en))
                f.write(pack_idx(rb.bone_index, b_size, True))
                f.write(struct.pack('<B', rb.group))
                f.write(struct.pack('<H', rb.non_collision_group_mask))
                f.write(struct.pack('<B', rb.shape_type))
                f.write(struct.pack('<3f', *rb.size))
                f.write(struct.pack('<3f', *rb.pos))
                f.write(struct.pack('<3f', *rb.rot))
                f.write(struct.pack('<f', rb.mass))
                f.write(struct.pack('<f', rb.linear_damping))
                f.write(struct.pack('<f', rb.angular_damping))
                f.write(struct.pack('<f', rb.restitution))
                f.write(struct.pack('<f', rb.friction))
                f.write(struct.pack('<B', rb.physics_type))

            # Joints
            f.write(struct.pack('<i', len(self.joints)))
            for j in self.joints:
                f.write(pack_str(j.name_jp))
                f.write(pack_str(j.name_en))
                f.write(struct.pack('<B', j.type))
                f.write(pack_idx(j.rigid_body_a, rb_size, True))
                f.write(pack_idx(j.rigid_body_b, rb_size, True))
                f.write(struct.pack('<3f', *j.pos))
                f.write(struct.pack('<3f', *j.rot))
                f.write(struct.pack('<3f', *j.pos_min))
                f.write(struct.pack('<3f', *j.pos_max))
                f.write(struct.pack('<3f', *j.rot_min))
                f.write(struct.pack('<3f', *j.rot_max))
                f.write(struct.pack('<3f', *j.pos_spring))
                f.write(struct.pack('<3f', *j.rot_spring))
