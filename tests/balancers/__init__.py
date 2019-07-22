import pytest

from needlestack.balancers import Item, Knapsack


def test_knapsack_add_item():
    item = Item("id", "value", weight=3.14)
    knapsack = Knapsack("id", "value")
    knapsack.add_item(item)
    assert item in knapsack.items
    assert knapsack.current_weight == 3.14


def test_knapsack_add_duplicate_item():
    item = Item("id", "value", weight=1.2)
    knapsack = Knapsack("id", "value")
    knapsack.add_item(item)
    with pytest.raises(ValueError) as excinfo:
        knapsack.add_item(item)
        assert "Item already exists in this knapsack" == str(excinfo.value)
