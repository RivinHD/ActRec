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


@pytest.fixture
def gppad_data(request):
    return [bpy.data.workspaces['Layout'].screens['Layout'].areas[0].spaces[0]]


@pytest.mark.parametrize("input, exclude, output",  # TODO more test Data
                         [(gppad_data[0], [],
                           {'type': 'PROPERTIES', 'show_locked_time': False, 'show_region_header': True,
                            'context': 'OBJECT', 'pin_id': None, 'use_pin_id': False,
                            'tab_search_results':
                            (False, False, False, False, False, False, False, False, False, False, False, False, False,
                             False, False, False, False, False, False),
                            'search_filter': '', 'outliner_sync': 'AUTO'})],
                         indirect=True)
def test_property_to_python(input, exclude, output):
    assert shared.property_to_python(input, exclude) == output


@pytest.fixture
def adti_data(request):
    return [bpy.data.workspaces['Layout'].screens['Layout'].areas[0].spaces[0]]


@pytest.mark.parametrize("input, data",
                         [(adti_data[0],
                           {'type': 'PROPERTIES', 'show_locked_time': True, 'show_region_header': False,
                            'context': 'DATA', 'pin_id': None, 'use_pin_id': False,
                            'tab_search_results':
                            (False, False, False, False, False, False, False, False, False, False, False, False, False,
                             False, False, False, False, False, False),
                             'search_filter': '', 'outliner_sync': 'AUTO'})],
                         indirect=True
                         )
def test_apply_data_to_item(input, data):
    shared.apply_data_to_item(input, data)
    assert helper.compare_with_dict(input, data)


@pytest.fixture
def adtoc_data(request):
    return [bpy.context.preferences.addons['cycles'].preferences.devices]


@pytest.mark.parametrize("collection, data",
                         [(adtoc_data[0], {'name': "test", 'id': "TT", 'use': False, 'type': "OPTIX"})],
                         indirect=True
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
