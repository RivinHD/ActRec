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
    return [bpy.data.workspaces['Layout'].screens['Layout'].areas[0].spaces[0]][request.param]


@pytest.mark.parametrize("gppad_data, exclude, output",  # TODO more test Data
                         [(0, [],
                           {'type': 'PROPERTIES', 'show_locked_time': False, 'show_region_header': True,
                            'context': 'OBJECT', 'pin_id': None, 'use_pin_id': False,
                            'tab_search_results':
                            (False, False, False, False, False, False, False, False, False, False, False, False, False,
                             False, False, False, False, False, False),
                            'search_filter': '', 'outliner_sync': 'AUTO'})],
                         indirect=True)
def test_property_to_python(gppad_data, exclude, output):
    assert shared.property_to_python(gppad_data, exclude) == output


@pytest.fixture
def adti_data(request):
    return [bpy.data.workspaces['Layout'].screens['Layout'].areas[0].spaces[0]][request.param]


@pytest.mark.parametrize("adti_data, data",
                         [(0,
                           {'type': 'PROPERTIES', 'show_locked_time': True, 'show_region_header': False,
                            'context': 'DATA', 'pin_id': None, 'use_pin_id': False,
                            'tab_search_results':
                            (False, False, False, False, False, False, False, False, False, False, False, False, False,
                             False, False, False, False, False, False),
                             'search_filter': '', 'outliner_sync': 'AUTO'})],
                         indirect=True
                         )
def test_apply_data_to_item(adti_data, data):
    shared.apply_data_to_item(adti_data, data)
    assert helper.compare_with_dict(adti_data, data)


@pytest.fixture
def adtoc_data(request):
    return [bpy.context.preferences.addons['cycles'].preferences.devices][request.param]


@pytest.mark.parametrize("adtoc_data, data",
                         [(0, {'name': "test", 'id': "TT", 'use': False, 'type': "OPTIX"})],
                         indirect=True
                         )
def test_add_data_to_collection(adtoc_data, data):
    length = len(adtoc_data)
    name = data['name']
    index = adtoc_data.find(name)
    shared.add_data_to_collection(adtoc_data, data)
    assert (
        length + 1 == len(adtoc_data)
        and index != -1
        and helper.compare_with_dict(adtoc_data[name], data)
    )
    adtoc_data.remove(index)
