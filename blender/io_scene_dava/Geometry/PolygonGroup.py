'''
Copyright (C) 2023 Pyogenics <https://www.github.com/Pyogenics>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from io import BytesIO

from ..FileIO.StreamBuffer import StreamBuffer

class VertexTypes:
    VERTEX = 1
    NORMAL = 1 << 1
    COLOR = 1 << 2
    TEXCOORD0 = 1 << 3
    TEXCOORD1 = 1 << 4
    TEXCOORD2 = 1 << 5
    TEXCOORD3 = 1 << 6
    TANGENT = 1 << 7
    BINORMAL = 1 << 8
    HARD_JOINTINDEX = 1 << 9
    PIVOT4 = 1 << 10
    FLEXIBILITY = 1 << 12
    ANGLE_SIN_COS = 1 << 13
    JOINTINDEX = 1 << 14
    JOINTWEIGHT = 1 << 15
    CUBETEXCOORD0 = 1 << 16
    CUBETEXCOORD1 = 1 << 17
    CUBETEXCOORD2 = 1 << 18
    CUBETEXCOORD3 = 1 << 19

class VertexFormat:
    def __init__(self, fmt):
        # Stride values
        self.stride = 0
        self.VERTX = -1
        self.NORMAL = -1
        self.COLOR = -1
        self.TEXCOORD0 = -1
        self.TEXCOORD1 = -1
        self.TEXCOORD2 = -1
        self.TEXCOORD3 = -1
        self.TANGENT = -1
        self.BINORMAL = -1
        self.HARD_JOINTINDEX = -1
        self.CUBETEXCOORD0 = -1
        self.CUBETEXCOORD1 = -1
        self.CUBETEXCOORD2 = -1
        self.CUBETEXCOORD3 = -1
        self.PIVOT4 = -1
        self.FLEXIBILITY = -1
        self.ANGLE_SIN_COS = -1
        self.JOINTINDEX = -1
        self.JOINTWEIGHT = -1

        # Parse format
        stride = 0
        if (fmt & VertexTypes.VERTEX):
            self.VERTEX = stride
            stride += 3 * 4
        if (fmt & VertexTypes.NORMAL):
            self.NORMAL = stride
            stride += 3 * 4
        if (fmt & VertexTypes.COLOR):
            self.COLOR = stride
            stride += 4
        if (fmt & VertexTypes.TEXCOORD0):
            self.TEXCOORD0 = stride
            stride += 2 * 4
        if (fmt & VertexTypes.TEXCOORD1):
            self.TEXCOORD1 = stride
            stride += 2 * 4
        if (fmt & VertexTypes.TEXCOORD2):
            self.TEXCOORD2 = stride
            stride += 2 * 4
        if (fmt & VertexTypes.TEXCOORD3):
            self.TEXCOORD3 = stride
            stride += 2 * 4

        if (fmt & VertexTypes.TANGENT):
            self.TANGENT = stride
            stride += 3 * 4
        if (fmt & VertexTypes.BINORMAL):
            self.BINORMAL = stride
            stride += 3 * 4
        if (fmt & VertexTypes.HARD_JOINTINDEX):
            self.HARD_JOINTINDEX = stride
            stride += 4

        if (fmt & VertexTypes.CUBETEXCOORD0):
            self.CUBETEXCOORD0 = stride
            stride += 3 * 4
        if (fmt & VertexTypes.CUBETEXCOORD1):
            self.CUBETEXCOORD1 = stride
            stride += 3 * 4
        if (fmt & VertexTypes.CUBETEXCOORD2):
            self.CUBETEXCOORD2 = stride
            stride += 3 * 4
        if (fmt & VertexTypes.CUBETEXCOORD3):
            self.CUBETEXCOORD3 = stride
            stride += 3 * 4

        if (fmt & VertexTypes.PIVOT4):
            self.PIVOT4 = stride
            stride += 4 * 4
        if (fmt & VertexTypes.FLEXIBILITY):
            self.FLEXIBILITY = stride
            stride += 4
        if (fmt & VertexTypes.ANGLE_SIN_COS):
            self.ANGLE_SIN_COS = stride
            stride += 2 * 4

        if (fmt & VertexTypes.JOINTINDEX):
            self.JOINTINDEX = stride
            stride += 4 * 4
        if (fmt & VertexTypes.JOINTWEIGHT):
            self.JOINTWEIGHT = stride
            stride += 4 * 4

        self.stride = stride

class PrimitiveTypes:
    TRIANGLELIST = 1
    TRIANGLESTRIP = 2
    LINELIST = 10

class PolygonGroup:
    def __init__(self, polyGroup):
        self.id = polyGroup["#id"]
        self.cubeTextureCoordCount = polyGroup["cubeTextureCoordCount"]
        self.primitiveType = polyGroup["rhi_primitiveType"]
        self.primitiveCount = polyGroup["primitiveCount"]

        # Vertices
        self.vertices = []
        self.normals = []
        self.colors = []
        self.texcoords = []
        self.tangents = []
        self.binormals = []
        self.hard_jointindices = []
        self.pivot4 = []
        self.flexibilities = []
        self.angles_sin_cos = []
        self.jointindices = []
        self.jointweights = []
        self.cubetexcoords = []
        self.uvs = []
        self.uv2s = []
        self.indices = []

        # Parse vertex format
        vertexFormat = VertexFormat(polyGroup["vertexFormat"])

        # Parse vertices TODO
        stream = StreamBuffer( BytesIO(polyGroup["vertices"]) )
        for _ in range(polyGroup["vertexCount"]):
            start_pos = stream.tell()
            if vertexFormat.VERTEX > -1:
                self.vertices.append(
                        (stream.readFloat(), stream.readFloat(), stream.readFloat())
                )
            if vertexFormat.NORMAL > -1:
                self.normals.append(
                    (stream.readFloat(), stream.readFloat(), stream.readFloat())
                )
            if vertexFormat.COLOR > -1:
                # Colors are usually 4 bytes (RGBA)
                self.colors.append(stream.readInt32())
            if vertexFormat.TEXCOORD0 > -1:
                self.uvs.append(
                    (stream.readFloat(), stream.readFloat())
                )
            if vertexFormat.TEXCOORD1 > -1:
                self.uv2s.append(
                    (stream.readFloat(), stream.readFloat())
                )
            if vertexFormat.TANGENT > -1:
                self.tangents.append(
                    (stream.readFloat(), stream.readFloat(), stream.readFloat())
                )
            if vertexFormat.BINORMAL > -1:
                self.binormals.append(
                    (stream.readFloat(), stream.readFloat(), stream.readFloat())
                )
            bytes_read = stream.tell() - start_pos
            if bytes_read < vertexFormat.stride:
                stream.readBytes(vertexFormat.stride - bytes_read)

        # Parse indices
        # 0 = uint16_t
        # 1 = uint32_t
        stream = StreamBuffer( BytesIO(polyGroup["indices"]) )
        self.indices = []
        if polyGroup["indexFormat"] == 0:
            for _ in range(polyGroup["indexCount"]): self.indices.append( stream.readInt16(False) )
        if polyGroup["indexFormat"] == 1:
            for _ in range(polyGroup["indexCount"]): self.indices.append( stream.readInt32(False) )

    '''
    Primitive builders

    line list, triangle list, triangle strip
    '''
    def getTriangleList(self):
        faceIndices = []
        for i in range(0, len(self.indices), 3):
            faceIndices.append([
                self.indices[i],
                self.indices[i+1],
                self.indices[i+2]
            ])

        return faceIndices

    #NOTE: We convert trianglestrip to trianglist to make the import easier
    def getTriangleStrip(self): 
        faceIndices = []

        # First triangle
        faceIndices.append([
            self.indices[0],
            self.indices[1],
            self.indices[2]
        ])

        # Digest triangestrip into trianglelist
        for i in range(3, len(self.indices)):
            faceIndices.append([
                self.indices[i-2],
                self.indices[i-1],
                self.indices[i]
            ])

        return faceIndices

    def getLineList(self):
        edgeIndices = []
        for i in range(0, len(self.indices), 2):
            edgeIndices.append([
                self.indices[i],
                self.indices[i+1]
            ])

        return edgeIndices

    def toArchive(self):
        """
        Serialise this PolygonGroup to a KA archive dict.
        Always does a full rebuild from the Blender mesh (_blender_mesh).
        Normals come from loop.normal — either the custom normals layer set at
        import (original geometry) or Blender-computed (new/joined geometry).
        Metadata (#id, vertexFormat, primitiveType etc.) preserved from raw_archive.
        """
        from io import BytesIO
        import struct as _struct

        raw          = getattr(self, '_raw_archive', None)
        blender_mesh = getattr(self, '_blender_mesh', None)

        if blender_mesh is None:
            raise RuntimeError("toArchive: _blender_mesh not set")

        mesh = blender_mesh

        # Metadata from raw_archive (preserved exactly), or sensible defaults
        orig_fmt     = raw["vertexFormat"]          if raw else None
        cube_tex     = raw["cubeTextureCoordCount"] if raw else 0
        prim_type    = raw["rhi_primitiveType"]     if raw else self.primitiveType
        packing      = raw["packing"]               if raw else 0
        has_color    = raw is not None and VertexFormat(raw["vertexFormat"]).COLOR >= 0

        # Default color — first vertex color from raw_archive, or white
        if has_color:
            vf_tmp = VertexFormat(raw["vertexFormat"])
            default_color = raw["vertices"][vf_tmp.COLOR : vf_tmp.COLOR + 4]
        else:
            default_color = b'\xff\xff\xff\xff'

        # UV layers
        uv_tex_layer = mesh.uv_layers.get("UVMap_Texture")  or (mesh.uv_layers[0]  if mesh.uv_layers       else None)
        uv_lm_layer  = mesh.uv_layers.get("UVMap_Lightmap") or (mesh.uv_layers[1]  if len(mesh.uv_layers)>1 else None)
        has_tangents = uv_tex_layer is not None

        # Build split-vertex table
        # Key: (vertex_index, uv_key, uv2_key) — one entry per unique loop combination
        vert_map  = {}
        positions = []
        normals   = []
        tangents  = []
        binormals = []
        uvs_out   = []
        uv2s_out  = []
        colors_b  = []
        indices   = []

        for tri in mesh.loop_triangles:
            face_idx = []
            for li in tri.loops:
                loop = mesh.loops[li]
                vi   = loop.vertex_index
                co   = mesh.vertices[vi].co

                uv_key  = None
                uv2_key = None
                if uv_tex_layer:
                    u, v = uv_tex_layer.data[li].uv
                    uv_key = (round(u, 6), round(v, 6))
                if uv_lm_layer:
                    u, v = uv_lm_layer.data[li].uv
                    uv2_key = (round(u, 6), round(v, 6))

                key = (vi, uv_key, uv2_key)
                if key not in vert_map:
                    vert_map[key] = len(positions)
                    positions.append((co.x, co.y, co.z))

                    n = loop.normal
                    normals.append((n.x, n.y, n.z))

                    if has_tangents:
                        t    = loop.tangent
                        sign = loop.bitangent_sign
                        bx   = (n.y*t.z - n.z*t.y) * sign
                        by   = (n.z*t.x - n.x*t.z) * sign
                        bz   = (n.x*t.y - n.y*t.x) * sign
                        tangents.append((t.x, t.y, t.z))
                        binormals.append((bx, by, bz))
                    else:
                        tangents.append((1.0, 0.0, 0.0))
                        binormals.append((0.0, 1.0, 0.0))

                    if uv_key:  uvs_out.append((uv_key[0], 1.0 - uv_key[1]))
                    if uv2_key: uv2s_out.append((uv2_key[0], 1.0 - uv2_key[1]))
                    colors_b.append(default_color)

                face_idx.append(vert_map[key])
            indices.extend(face_idx)

        # Vertex format — preserve original if available
        fmt = VertexTypes.VERTEX | VertexTypes.NORMAL
        if has_color:    fmt |= VertexTypes.COLOR
        if uvs_out:      fmt |= VertexTypes.TEXCOORD0
        if uv2s_out:     fmt |= VertexTypes.TEXCOORD1
        if has_tangents: fmt |= VertexTypes.TANGENT | VertexTypes.BINORMAL
        if orig_fmt is not None:
            fmt = orig_fmt

        vf_out  = VertexFormat(fmt)
        n_verts = len(positions)

        # Pack vertex buffer
        import struct as _st
        vbuf = BytesIO()
        for i in range(n_verts):
            if vf_out.VERTEX   >= 0: vbuf.write(_st.pack('<fff', *positions[i]))
            if vf_out.NORMAL   >= 0: vbuf.write(_st.pack('<fff', *normals[i]))
            if vf_out.COLOR    >= 0: vbuf.write(colors_b[i])
            if vf_out.TEXCOORD0 >= 0 and i < len(uvs_out):
                vbuf.write(_st.pack('<ff', *uvs_out[i]))
            if vf_out.TEXCOORD1 >= 0 and i < len(uv2s_out):
                vbuf.write(_st.pack('<ff', *uv2s_out[i]))
            if vf_out.TANGENT  >= 0: vbuf.write(_st.pack('<fff', *tangents[i]))
            if vf_out.BINORMAL >= 0: vbuf.write(_st.pack('<fff', *binormals[i]))

        # Pack index buffer
        max_idx = max(indices) if indices else 0
        if max_idx <= 0xFFFF:
            index_fmt   = 0
            index_bytes = _st.pack(f'<{len(indices)}H', *indices)
        else:
            index_fmt   = 1
            index_bytes = _st.pack(f'<{len(indices)}I', *indices)

        # #id
        id_src = raw["#id"] if raw else self.id
        if isinstance(id_src, (bytes, bytearray)) and len(id_src) == 8:
            id_bytes = bytes(id_src)
        elif isinstance(id_src, (bytes, bytearray)) and len(id_src) == 4:
            id_bytes = bytes(id_src) + b'\x00\x00\x00\x00'
        else:
            iv = id_src if isinstance(id_src, int) else 0
            id_bytes = iv.to_bytes(8, byteorder='little', signed=False)

        tex_coord_count = (1 if uvs_out else 0) + (1 if uv2s_out else 0)

        return {
            "##name":                "PolygonGroup",
            "#id":                   id_bytes,
            "cubeTextureCoordCount": cube_tex,
            "indexCount":            len(indices),
            "indexFormat":           index_fmt,
            "indices":               index_bytes,
            "packing":               packing,
            "primitiveCount":        len(indices) // 3,
            "rhi_primitiveType":     prim_type,
            "textureCoordCount":     tex_coord_count,
            "vertexCount":           n_verts,
            "vertexFormat":          fmt,
            "vertices":              vbuf.getvalue(),
        }

    @staticmethod
    def fromBlenderMesh(mesh_obj, groupID, primitiveType=None):
        """
        Build a PolygonGroup from a Blender mesh object.
        Always evaluates the mesh fully — normals come from the custom normals
        layer (set at import) or Blender-computed (new geometry).
        raw_archive is used only for metadata preservation.
        """
        import bpy, json, re as _re

        print(f"=== fromBlenderMesh: '{mesh_obj.name}' ===")

        # Restore raw_archive (metadata only)
        raw_json = mesh_obj.get("dava_raw_archive", None)
        raw = None
        if raw_json is not None:
            try:
                raw_dict = json.loads(raw_json)
                for key in ("vertices", "indices", "#id"):
                    if key in raw_dict and isinstance(raw_dict[key], str):
                        raw_dict[key] = bytes.fromhex(raw_dict[key])
                raw = raw_dict
            except Exception as e:
                print(f"=== raw_archive restore failed: {e} ===")

        # Recover #id
        _dava_id = mesh_obj.get("dava_id", None)
        if _dava_id is not None:
            _id_bytes = bytes.fromhex(_dava_id) if isinstance(_dava_id, str) else bytes(_dava_id)
        else:
            _m        = _re.search(r'(\d+)$', mesh_obj.name)
            _id_int   = int(_m.group(1)) if _m else groupID
            _id_bytes = _id_int.to_bytes(8, byteorder='little', signed=False)

        # Evaluate mesh (applies modifiers, bakes transforms for auto-join path)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval  = mesh_obj.evaluated_get(depsgraph)
        try:
            eval_mesh = obj_eval.to_mesh()
            eval_mesh.calc_loop_triangles()
            # calc_tangents uses the custom normals layer automatically
            uv_tex = eval_mesh.uv_layers.get("UVMap_Texture") or (
                eval_mesh.uv_layers[0] if eval_mesh.uv_layers else None)
            if uv_tex:
                try:
                    eval_mesh.calc_tangents(uvmap=uv_tex.name)
                except Exception as e:
                    print(f"=== calc_tangents failed: {e} ===")
        except Exception as e:
            obj_eval.to_mesh_clear()
            raise RuntimeError(f"Mesh evaluation failed: {e}")

        # Build shell
        pg = PolygonGroup.__new__(PolygonGroup)
        pg.id                    = _id_bytes
        pg.primitiveType         = primitiveType if primitiveType is not None else PrimitiveTypes.TRIANGLELIST
        pg.primitiveCount        = 0
        pg.cubeTextureCoordCount = 0
        pg.vertices = []; pg.normals = []; pg.colors = []
        pg.tangents = []; pg.binormals = []
        pg.hard_jointindices = []; pg.pivot4 = []; pg.flexibilities = []
        pg.angles_sin_cos = []; pg.jointindices = []; pg.jointweights = []
        pg.cubetexcoords = []; pg.indices = []
        pg._raw_archive  = raw
        pg._blender_mesh = eval_mesh
        pg._obj_eval     = obj_eval
        return pg

    def release_blender_mesh(self):
        """Free the evaluated mesh after toArchive()."""
        if self._obj_eval is not None:
            try: self._obj_eval.to_mesh_clear()
            except Exception: pass
        self._obj_eval     = None
        self._blender_mesh = None

