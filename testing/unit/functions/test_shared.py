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


# FIXME use own defined preferences properties to test with, hopefully no access violation by using them
""" # access violation
@pytest.mark.parametrize("property_str, exclude, output",  # TODO more test Data
                         [("bpy.data.workspaces['Layout'].screens['Layout'].areas[0].spaces[0]", [],
                           {'type': 'PROPERTIES', 'show_locked_time': False, 'show_region_header': True,
                            'context': 'OBJECT', 'pin_id': None, 'use_pin_id': False,
                            'tab_search_results':
                            (False, False, False, False, False, False, False, False, False, False, False, False, False,
                             False, False, False, False, False, False),
                            'search_filter': '', 'outliner_sync': 'AUTO'})]
                         )
def test_property_to_python(property_str, exclude, output):
    property = eval(property_str)
    assert shared.property_to_python(property, exclude) == output
"""


@pytest.fixture(scope="function")
def apply_data(request):
    helper.get_pref_data(request.param.split(".")[0].split("[")[0]).clear()
    helper.load_global_actions_test_data(shared.get_preferences(bpy.context))
    print(shared.get_preferences(bpy.context).global_actions.keys())
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
