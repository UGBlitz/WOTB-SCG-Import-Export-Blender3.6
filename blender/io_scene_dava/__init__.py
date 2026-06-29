'''
Copyright (C) 2023 Pyogenics <https://www.github.com/Pyogenics>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

bl_info = {
    "name": "DAVA Scene File format",
    "description": "Support for DAVA framework scene files",
    "author": "Pyogenics, https://www.github.com/Pyogenics",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "File > Import-Export",
    "doc_url": "https://github.com/Pyogenics/SCPG-reverse-engineering",
    "tracker_url": "https://github.com/Pyogenics/SCPG-reverse-engineering/issues",
    "category": "Import-Export"
}

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .FileIO.StreamBuffer import StreamBuffer
from .FileIO.SCG import readSCG, writeSCG
from .Geometry.PolygonGroup import PrimitiveTypes, PolygonGroup

'''
Operators
'''
class ImportDAVA(Operator, ImportHelper):
    bl_idname = "import_scene.scg"
    bl_label = "Import DAVA geometry"
    bl_description = "Import a DAVA scene file"

    filter_glob: StringProperty(default="*.scg", options={'HIDDEN'})

    def invoke(self, context, event):
        return ImportHelper.invoke(self, context, event)

    # Just import SCG whilst we get proper full imports working
    def execute(self, context):
        filepath = self.filepath
        print(f"Importing DAVA scene from {filepath}")
        
        with open(filepath, "rb") as scg:
            polyGroups = readSCG(
                StreamBuffer(scg)
            )

            # Keep raw archives before parsing (exporter needs them to patch UVs)
            polyGroups_raw = {gid: dict(raw) for gid, raw in polyGroups.items()}
            # Parse polygon groups
            for groupID in polyGroups.keys():
                polyGroups[groupID] = PolygonGroup( polyGroups[groupID] )

            # Add polygon groups to scene
            collection = bpy.data.collections.new("DAVAMesh")
            for groupID in polyGroups.keys():
                group = polyGroups[groupID]
                mesh = bpy.data.meshes.new("mesh")

                if group.primitiveType == PrimitiveTypes.TRIANGLELIST:
                    mesh.from_pydata(group.vertices, [], group.getTriangleList())
                elif group.primitiveType == PrimitiveTypes.TRIANGLESTRIP:
                    mesh.from_pydata(group.vertices, [], group.getTriangleStrip())
                elif group.primitiveType == PrimitiveTypes.LINELIST:
                    mesh.from_pydata(group.vertices, group.getLineList(), [])
                
                if hasattr(group, 'uvs') and len(group.uvs) > 0:
                    uv_layer = mesh.uv_layers.new(name="UVMap_Texture")
                    for loop in mesh.loops:
                        uv = group.uvs[loop.vertex_index]
                        uv_layer.data[loop.index].uv = (uv[0], 1.0 - uv[1])
                
                if hasattr(group, 'uv2s') and len(group.uv2s) > 0:
                    lm_layer = mesh.uv_layers.new(name="UVMap_Lightmap")
                    for loop in mesh.loops:
                        lm = group.uv2s[loop.vertex_index]
                        lm_layer.data[loop.index].uv = (lm[0], 1.0 - lm[1])

                # Store original normals as a Blender custom normals layer.
                # This means loop.normal always returns the correct DAVA normal
                # without any raw_archive lookup — survives joins, moves, UV edits.
                if hasattr(group, 'normals') and len(group.normals) > 0:
                    mesh.update()  # must call before normals_split_custom_set
                    # Build per-loop normals: each loop's normal = its vertex's normal
                    loop_normals = [(0.0, 0.0, 1.0)] * len(mesh.loops)
                    for loop in mesh.loops:
                        vi = loop.vertex_index
                        if vi < len(group.normals):
                            loop_normals[loop.index] = tuple(group.normals[vi])
                    mesh.normals_split_custom_set(loop_normals)
                    mesh.use_auto_smooth = True   # required for custom normals to take effect
                else:
                    mesh.update()

                obj = bpy.data.objects.new(f"PolygonGroup{groupID}", mesh)
                # Store raw archive so the exporter can patch UVs into the
                # original vertex buffer (preserving normals, tangents, etc.)
                import json
                raw = polyGroups_raw[groupID]
                obj["dava_raw_archive"] = json.dumps({
                    k: v.hex() if isinstance(v, (bytes, bytearray)) else v
                    for k, v in raw.items()
                })
                # Store #id separately so objects can be freely renamed
                obj["dava_id"] = raw["#id"].hex() if isinstance(raw["#id"], (bytes, bytearray)) else raw["#id"]
                collection.objects.link(obj)
            bpy.context.scene.collection.children.link(collection)
            self.report({"INFO"}, f"Loaded {len(polyGroups)} polygon groups")

        return {"FINISHED"}

class ExportDAVA(Operator, ExportHelper):
    bl_idname = "export_scene.scg"
    bl_label = "Export DAVA geometry"
    bl_description = "Export selected meshes as a DAVA .scg geometry file"

    # filename_ext MUST be a plain class string — ExportHelper reads it as an
    # attribute to append to the filename. A StringProperty here crashes Blender.
    filename_ext = ".scg"

    filter_glob: StringProperty(default="*.scg", options={'HIDDEN'})

    def invoke(self, context, event):
        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        import traceback
        print("=== DAVA Export: execute() started ===")

        filepath = self.filepath
        print(f"=== DAVA Export: filepath = {filepath!r} ===")

        try:
            objects = [o for o in context.selected_objects if o.type == 'MESH']
            if not objects:
                objects = [o for o in context.scene.objects if o.type == 'MESH']
            print(f"=== DAVA Export: found {len(objects)} mesh objects ===")

            if not objects:
                self.report({'WARNING'}, "No mesh objects found to export")
                return {'CANCELLED'}

            import re as _re

            # ── Auto-join: merge xyz_abc into xyz before export ───────────────
            # Objects named "xyz_abc" (one underscore, no underscore in base)
            # are treated as attachments to their parent "xyz".
            # We build a virtual merged mesh per parent without touching the scene.

            # Separate parents from attachments
            def _base_name(name):
                """Return base if name matches pattern 'base_suffix', else None."""
                m = _re.match(r'^([^_]+)_([^_]+)$', name)
                return m.group(1) if m else None

            all_by_name = {o.name: o for o in objects}
            attachments = {}   # parent_name -> [attachment_obj, ...]
            parents_with_attach = set()

            for obj in objects:
                base = _base_name(obj.name)
                if base and base in all_by_name:
                    attachments.setdefault(base, []).append(obj)
                    parents_with_attach.add(base)

            # Objects that are pure attachments are not exported standalone
            attachment_names = {o.name for objs in attachments.values() for o in objs}
            primary_objects  = [o for o in objects if o.name not in attachment_names]

            # Sort primaries by dava_id
            def _sort_key(obj):
                dava_id = obj.get("dava_id", None)
                if dava_id is not None:
                    id_bytes = bytes.fromhex(dava_id) if isinstance(dava_id, str) else bytes(dava_id)
                    return int.from_bytes(id_bytes, "little")
                m = _re.search(r'(\d+)$', obj.name)
                return int(m.group(1)) if m else 0
            primary_objects.sort(key=_sort_key)

            # ── Virtual join: build a temporary merged mesh for each parent ──
            # Uses bmesh to merge geometry in Python — never modifies the scene.
            import bmesh

            def _make_merged_mesh(parent_obj, attach_objs):
                """Return a temporary bpy.data.Mesh combining parent + attachments.
                   The parent's vertex data comes first so its indices are preserved
                   for Mode-A UV patching. Custom properties are NOT copied — the
                   caller uses parent_obj's properties directly."""
                import bpy
                bm = bmesh.new()

                # Parent first — its vertices occupy indices 0..N-1
                parent_mesh = parent_obj.evaluated_get(
                    bpy.context.evaluated_depsgraph_get()).to_mesh()
                bm.from_mesh(parent_mesh)
                parent_obj.evaluated_get(
                    bpy.context.evaluated_depsgraph_get()).to_mesh_clear()

                # Attachments appended after
                depsgraph = bpy.context.evaluated_depsgraph_get()
                for att in attach_objs:
                    att_eval = att.evaluated_get(depsgraph)
                    att_mesh = att_eval.to_mesh()
                    bm.from_mesh(att_mesh)
                    att_eval.to_mesh_clear()

                merged = bpy.data.meshes.new("__dava_merged_tmp__")
                bm.to_mesh(merged)
                bm.free()

                # Copy UV layers from parent mesh into merged mesh
                # We rebuild UV data by iterating merged loops and mapping back
                # to original vertex index where possible
                # UV layers are rebuilt by fromBlenderMesh from the merged mesh loops
                # so we need to transfer them properly

                # Transfer UVMap_Texture
                _transfer_uvs(parent_obj, attach_objs, merged)

                return merged

            def _transfer_uvs(parent_obj, attach_objs, merged_mesh):
                """Copy UV data from parent and attachments into the merged mesh.
                   Vertices are ordered: parent verts first, then each attachment."""
                import bpy

                # Count parent verts (evaluated)
                depsgraph = bpy.context.evaluated_depsgraph_get()
                p_eval = parent_obj.evaluated_get(depsgraph)
                p_mesh_tmp = p_eval.to_mesh()
                p_nv = len(p_mesh_tmp.vertices)
                p_eval.to_mesh_clear()

                # Build vert_count list: [parent_count, att1_count, att2_count, ...]
                vert_counts = [p_nv]
                att_nv_list = []
                for att in attach_objs:
                    a_eval = att.evaluated_get(depsgraph)
                    a_mesh_tmp = a_eval.to_mesh()
                    att_nv_list.append(len(a_mesh_tmp.vertices))
                    vert_counts.append(len(a_mesh_tmp.vertices))
                    a_eval.to_mesh_clear()

                # For each UV layer name present in any source, create in merged
                uv_sources = {}  # layer_name -> list of (source_mesh_or_None, vert_offset)
                all_uv_names = set()

                # gather from parent
                p_mesh_ref = parent_obj.data
                for ul in p_mesh_ref.uv_layers:
                    all_uv_names.add(ul.name)
                for att in attach_objs:
                    for ul in att.data.uv_layers:
                        all_uv_names.add(ul.name)

                for uv_name in all_uv_names:
                    uv_layer = merged_mesh.uv_layers.new(name=uv_name)
                    # Build a vi -> uv map for parent
                    p_uv_src = p_mesh_ref.uv_layers.get(uv_name)
                    p_vi_to_uv = {}
                    if p_uv_src:
                        for loop in p_mesh_ref.loops:
                            vi = loop.vertex_index
                            if vi not in p_vi_to_uv:
                                p_vi_to_uv[vi] = tuple(p_uv_src.data[loop.index].uv)

                    # Build vi->uv maps for each attachment
                    att_vi_to_uv = []
                    for att in attach_objs:
                        a_uv_src = att.data.uv_layers.get(uv_name)
                        a_map = {}
                        if a_uv_src:
                            for loop in att.data.loops:
                                vi = loop.vertex_index
                                if vi not in a_map:
                                    a_map[vi] = tuple(a_uv_src.data[loop.index].uv)
                        att_vi_to_uv.append(a_map)

                    # Write UVs into merged mesh loops
                    # merged_mesh.vertices[vi]: vi < p_nv -> parent, else attachment
                    offset = p_nv
                    att_offsets = []
                    for nv in att_nv_list:
                        att_offsets.append(offset)
                        offset += nv

                    for loop in merged_mesh.loops:
                        vi = loop.vertex_index
                        uv = (0.0, 0.0)
                        if vi < p_nv:
                            uv = p_vi_to_uv.get(vi, (0.0, 0.0))
                        else:
                            for ai, (att_off, a_map) in enumerate(zip(att_offsets, att_vi_to_uv)):
                                next_off = att_offsets[ai+1] if ai+1 < len(att_offsets) else offset
                                if att_off <= vi < next_off:
                                    local_vi = vi - att_off
                                    uv = a_map.get(local_vi, (0.0, 0.0))
                                    break
                        uv_layer.data[loop.index].uv = uv

            # ── Build archives ─────────────────────────────────────────────────
            archives = []
            tmp_meshes = []

            for groupID, obj in enumerate(primary_objects):
                print(f"=== DAVA Export: processing '{obj.name}' ===")
                try:
                    attached = attachments.get(obj.name, [])
                    if attached:
                        # Auto-join: build a temporary merged mesh in memory
                        print(f"=== DAVA Export: auto-joining {[a.name for a in attached]} into '{obj.name}' ===")
                        merged = _make_merged_mesh(obj, attached)
                        tmp_meshes.append(merged)
                        import bpy, json
                        dummy = bpy.data.objects.new("__dava_dummy__", merged)
                        # Copy custom properties from primary so dava_id/dava_raw_archive are available
                        for k, v in obj.items():
                            dummy[k] = v
                        dummy.name = obj.name
                        bpy.context.scene.collection.objects.link(dummy)
                        try:
                            pg = PolygonGroup.fromBlenderMesh(dummy, groupID)
                            archive = pg.toArchive()
                            pg.release_blender_mesh()
                        finally:
                            bpy.context.scene.collection.objects.unlink(dummy)
                            bpy.data.objects.remove(dummy)
                    else:
                        pg = PolygonGroup.fromBlenderMesh(obj, groupID)
                        archive = pg.toArchive()
                        pg.release_blender_mesh()

                    archives.append(archive)
                    print(f"=== DAVA Export: '{obj.name}' OK ===")
                except Exception as e:
                    print(f"=== DAVA Export: '{obj.name}' FAILED: {e} ===")
                    traceback.print_exc()
                    self.report({'WARNING'}, f"Skipping '{obj.name}': {e}")

            # Clean up temporary merged meshes
            import bpy as _bpy
            for m in tmp_meshes:
                try: _bpy.data.meshes.remove(m)
                except Exception: pass

            if not archives:
                self.report({'ERROR'}, "No polygon groups could be built")
                return {'CANCELLED'}

            print(f"=== DAVA Export: writing {len(archives)} groups to file ===")
            with open(filepath, "wb") as f:
                stream = StreamBuffer(f)
                writeSCG(stream, archives)
            print("=== DAVA Export: write complete ===")

        except Exception as e:
            print(f"=== DAVA Export: OUTER EXCEPTION: {e} ===")
            traceback.print_exc()
            self.report({'ERROR'}, f"Export failed: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Exported {len(archives)} polygon group(s) to {filepath}")
        return {'FINISHED'}

'''
Menu
'''
def menu_func_import_dava(self, context):
    self.layout.operator(ImportDAVA.bl_idname, text="DAVA scene (.sc2/.scg)")

def menu_func_export_dava(self, context):
    self.layout.operator(ExportDAVA.bl_idname, text="DAVA scene (.sc2/.scg)")

'''
Register
'''
classes = {
    ExportDAVA,
    ImportDAVA
}

def register():
    # Register classes
    for c in classes:
        bpy.utils.register_class(c)
    # File > Import-Export
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_dava)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_dava)

def unregister():
    # Unregister classes
    for c in classes:
        bpy.utils.unregister_class(c)
    # Remove `File > Import-Export`
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_dava)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_dava)
