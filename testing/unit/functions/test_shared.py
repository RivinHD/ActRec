import pytest
from ActRec.actrec.functions import shared
import bpy
import helper


@pytest.mark.parametrize(
    "check_list, name, output",
    [
        ([], "test", "test"),
        (["test"], "test", "test.001"),
        (["test", "test.001"], "test", "test.002"),
        (["test", "test.001", "test.002"], "test", "test.003"),
        (["test", "Ho", "something", "this", "there"], "name", "name"),
        ([], "", ""),
        ([""], "name", "name")
    ]
)
def test_check_for_duplicates(check_list, name, output):
    assert shared.check_for_duplicates(check_list, name) == output


@pytest.fixture(scope="function")
def to_python_data(request):
    pref = shared.get_preferences(bpy.context)
    pref.global_actions.clear()
    helper.load_global_actions_test_data(pref)
    return helper.get_pref_data(request.param)


@pytest.mark.parametrize(
    "to_python_data, exclude, output",  # TODO more test Data
    [
        ('global_actions["c7a1f271164611eca91770c94ef23b30"].macros["c7a3dcba164611ecaaec70c94ef23b30"]', [],
         {
            "name": "c7a3dcba164611ecaaec70c94ef23b30",
            "id": "c7a3dcba164611ecaaec70c94ef23b30",
            "label": "Delete",
            "command": "bpy.ops.object.delete(use_global=False)",
            "active": True,
            "icon": 0,
            "is_available": True,
            "ui_type: ": ""
        }),
        ('global_actions["c7a40353164611ecbaad70c94ef23b30"]',
         ["name", "selected", "alert", "macros.name", "macros.is_available", "macros.alert"],
         {
             "id": "c7a40353164611ecbaad70c94ef23b30",
             "label": "Subd Smooth",
             "macros": [
                 {
                     "id": "c7a40354164611ecb05c70c94ef23b30",
                     "label": "Subdivision Set",
                     "command": "bpy.ops.object.subdivision_set(level=1, relative=False)",
                     "active": True,
                     "icon": 0
                 },
                 {
                     "id": "c7a40355164611ecb9cd70c94ef23b30",
                     "label": "Shade Smooth",
                     "command": "bpy.ops.object.shade_smooth()",
                     "active": True,
                     "icon": 0
                 },
                 {
                     "id": "c7a42aa4164611ecba6570c94ef23b30",
                     "label": "Auto Smooth = True",
                     "command": "bpy.context.object.data.use_auto_smooth = True",
                     "active": True,
                     "icon": 0
                 },
                 {
                     "id": "c7a6be1e164611ec8ede70c94ef23b30",
                     "label": "Auto Smooth Angle = 3.14159",
                     "command": "bpy.context.object.data.auto_smooth_angle = 3.14159",
                     "active": True,
                     "icon": 0
                 }
             ],
             "icon": 127
         })]
)
def test_property_to_python(to_python_data, exclude, output):
    assert shared.property_to_python(to_python_data, exclude) == output


@pytest.fixture(scope="function")
def apply_data(request):
    pref = shared.get_preferences(bpy.context)
    pref.global_actions.clear()
    helper.load_global_actions_test_data(pref)
    if request.param == 'global_actions["c7a1f271164611eca91770c94ef23b30"]':
        pref.global_actions["c7a1f271164611eca91770c94ef23b30"].macros.clear()
    return helper.get_pref_data(request.param)


@pytest.mark.parametrize(
    "apply_data, data",
    [('global_actions["c7a1f271164611eca91770c94ef23b30"].macros["c7a3dcba164611ecaaec70c94ef23b30"]',
      {"id": "c7a3dcba164611ecaaec70c94ef23b30", "label": "Something",
       "command": "bpy.ops.object.delete(use_global=False)", "active": False, "icon": 15, "ui_type": ""}),
     ('global_actions["c7a1f271164611eca91770c94ef23b30"]',
      {"id": "c7a1f271164611eca91770c94ef23b30", "label": "Something",
       "macros":
       [{"id": "c7a3dcba164611ecaaec70c94ef23b30", "label": "Delete",
         "command": "bpy.ops.object.delete(use_global=False)", "active": False, "icon": 26, "ui_type": ""}],
       "icon": 7})],
    indirect=["apply_data"]
)
def test_apply_data_to_item(apply_data, data):
    shared.apply_data_to_item(apply_data, data)
    assert helper.compare_with_dict(apply_data, data)


@pytest.mark.parametrize("collection, data",
                         [(bpy.context.preferences.addons['cycles'].preferences.devices,
                           {'name': "test", 'id': "TT", 'use': False, 'type': "OPTIX"})]
                         )
def test_add_data_to_collection(collection, data):
    length = len(collection)
    name = data['name']
    shared.add_data_to_collection(collection, data)
    index = collection.find(name)
    assert (
        length + 1 == len(collection)
        and index != -1
        and helper.compare_with_dict(collection[name], data)
    )
    collection.remove(index)
