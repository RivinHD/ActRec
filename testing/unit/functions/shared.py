import pytest
from ActRec.actrec.functions import shared


@pytest.mark.parametrize(
    "check_list, name, output",
    [
        ([], "test", "test"),
        (["test"], "test", "test.001")
        (["test", "test.001"], "test", "test.002")
        (["test", "test.001", "test.002"], "test", "test.003")
        (["test", "Ho", "something", "this", "there"], "name", "name")
        ([], "", "")
        ([""], "name", "name")
    ]
)
def test_check_for_duplicates(check_list, name, output):
    assert shared.check_for_duplicates(check_list, name) == output
