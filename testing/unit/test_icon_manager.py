import pytest
from ...actrec import icon_manager


@pytest.mark.parametrize(
    ("input, output",
        [
            (212, 212),
            ("sefsfse", 101),
            (None, 101),
            ("TRASH", 21)
        ]
     )
)
def test_check_icon(input, output):
    assert icon_manager.check_icon(input) == output


if __name__ == "__main__":
    pytest.main()
