from peerfeedback.utils import get_pseudo_names


def test_alternate_names_cycles_through_names():
    names = get_pseudo_names()
    assert len(names) == 25
