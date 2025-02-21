# BlenderBIM Add-on - OpenBIM Blender Add-on
# Copyright (C) 2020, 2021 Dion Moult <dion@thinkmoult.com>
#
# This file is part of BlenderBIM Add-on.
#
# BlenderBIM Add-on is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BlenderBIM Add-on is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BlenderBIM Add-on.  If not, see <http://www.gnu.org/licenses/>.

import bpy
import ifcopenshell.api
import blenderbim.core.spatial
import blenderbim.tool as tool
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty
from mathutils import Vector
from blenderbim.bim.ifc import IfcStore


def add_object(self, context):
    obj = bpy.data.objects.new("Grid", None)
    obj.name = "Grid"

    collection = bpy.data.collections.new(obj.name)
    has_site_collection = False
    for child in context.view_layer.layer_collection.children:
        if "IfcProject/" not in child.name:
            continue
        for grandchild in child.children:
            if "IfcSite/" not in grandchild.name:
                continue
            has_site_collection = True
            grandchild.collection.children.link(collection)
            break
    if not has_site_collection:
        context.view_layer.active_layer_collection.collection.children.link(collection)
    collection.objects.link(obj)

    self.file = IfcStore.get_file()
    if self.file:
        bpy.ops.bim.assign_class(obj=obj.name, ifc_class="IfcGrid")
        collection.name = obj.name
        grid = self.file.by_id(obj.BIMObjectProperties.ifc_definition_id)
        if has_site_collection:
            site_obj = bpy.data.objects.get(grandchild.name)
            if site_obj and site_obj.BIMObjectProperties.ifc_definition_id:
                blenderbim.core.spatial.assign_container(
                    tool.Ifc, tool.Collector, tool.Spatial, structure_obj=site_obj, element_obj=obj
                )

    axes_collection = bpy.data.collections.new("UAxes")
    collection.children.link(axes_collection)
    for i in range(0, self.total_u):
        verts = [
            Vector((-2, i * self.u_spacing, 0)),
            Vector((((self.total_v - 1) * self.v_spacing) + 2, i * self.u_spacing, 0)),
        ]
        edges = [[0, 1]]
        faces = []
        mesh = bpy.data.meshes.new(name="Grid Axis")
        mesh.from_pydata(verts, edges, faces)
        tag = chr(ord("A") + i)
        obj = bpy.data.objects.new(f"IfcGridAxis/{tag}", mesh)

        axes_collection.objects.link(obj)

        if self.file:
            result = ifcopenshell.api.run(
                "grid.create_grid_axis",
                self.file,
                **{"axis_tag": tag, "uvw_axes": "UAxes", "grid": grid},
            )
            IfcStore.link_element(result, obj)
            ifcopenshell.api.run("grid.create_axis_curve", self.file, **{"axis_curve": obj, "grid_axis": result})
            obj.BIMObjectProperties.ifc_definition_id = result.id()

    axes_collection = bpy.data.collections.new("VAxes")
    collection.children.link(axes_collection)
    for i in range(0, self.total_v):
        verts = [
            Vector((i * self.v_spacing, -2, 0)),
            Vector((i * self.v_spacing, ((self.total_u - 1) * self.u_spacing) + 2, 0)),
        ]
        edges = [[0, 1]]
        faces = []
        mesh = bpy.data.meshes.new(name="Grid Axis")
        mesh.from_pydata(verts, edges, faces)
        tag = str(i + 1).zfill(2)
        obj = bpy.data.objects.new(f"IfcGridAxis/{tag}", mesh)

        axes_collection.objects.link(obj)

        if self.file:
            result = ifcopenshell.api.run(
                "grid.create_grid_axis",
                self.file,
                **{"axis_tag": tag, "uvw_axes": "VAxes", "grid": grid},
            )
            IfcStore.link_element(result, obj)
            ifcopenshell.api.run("grid.create_axis_curve", self.file, **{"axis_curve": obj, "grid_axis": result})
            obj.BIMObjectProperties.ifc_definition_id = result.id()


class BIM_OT_add_object(Operator):
    bl_idname = "mesh.add_grid"
    bl_label = "Grid"
    bl_options = {"REGISTER", "UNDO"}

    u_spacing: FloatProperty(name="U Spacing", default=10)
    total_u: IntProperty(name="Number of U Grids", default=3)
    v_spacing: FloatProperty(name="V Spacing", default=10)
    total_v: IntProperty(name="Number of V Grids", default=3)

    def execute(self, context):
        return IfcStore.execute_ifc_operator(self, context)

    def _execute(self, context):
        add_object(self, context)
        return {"FINISHED"}


def add_object_button(self, context):
    self.layout.operator(BIM_OT_add_object.bl_idname, icon="PLUGIN")
