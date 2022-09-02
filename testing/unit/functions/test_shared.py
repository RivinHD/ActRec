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


@pytest.mark.parametrize("property, data",
                         [(bpy.data.workspaces['Layout'].screens['Layout'].areas[0].spaces[0],
                           {'type': 'PROPERTIES', 'show_locked_time': True, 'show_region_header': False,
                            'context': 'DATA', 'pin_id': None, 'use_pin_id': False,
                            'tab_search_results':
                            (False, False, False, False, False, False, False, False, False, False, False, False, False,
                             False, False, False, False, False, False),
                            'search_filter': '', 'outliner_sync': 'AUTO'})]
                         )
def test_apply_data_to_item(property, data):
    shared.apply_data_to_item(property, data)
    assert helper.compare_with_dict(property, data)


@pytest.mark.parametrize("collection, data",
                         [(bpy.context.preferences.addons['cycles'].preferences.devices,
                           {'name': "test", 'id': "TT", 'use': False, 'type': "OPTIX"})]
                         )
def test_add_data_to_collection(collection, data):
    length = len(collection)
    name = data['name']
    index = collection.find(name)
    shared.add_data_to_collection(collection, data)
    assert (
        length + 1 == len(collection)
        and index != -1
        and helper.compare_with_dict(collection[name], data)
    )
    collection.remove(index)
