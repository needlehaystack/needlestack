from needlestack.balancers import Item, Knapsack
from needlestack.balancers import greedy


def test_greedy_solver_one_knapsack():
    item = Item("id", "value")
    knapsack = Knapsack("id", "value")
    greedy.solver([item], [knapsack])
    assert item in knapsack.items


def test_greedy_solver_two_knapsack():
    items = [Item("id", "value"), Item("id", "value")]
    knapsacks = [Knapsack("id", "value"), Knapsack("id", "value")]
    greedy.solver(items, knapsacks)
    for knapsack in knapsacks:
        assert len(knapsack.items) == 1


def test_greedy_solver_item_quantity_to_much():
    item_2x = Item("id", "value", quantity=2)
    knapsack = Knapsack("id", "value")
    greedy.solver([item_2x], [knapsack])
    assert len(knapsack.items) == 1


def test_greedy_solver_item_quantity():
    item_2x = Item("id", "value", quantity=2)
    item_3x = Item("id", "value", quantity=3)
    items = [item_2x, item_3x]
    knapsacks = [
        Knapsack("id", "value"),
        Knapsack("id", "value"),
        Knapsack("id", "value"),
    ]
    greedy.solver(items, knapsacks)
    for knapsack in knapsacks:
        assert item_3x in knapsack.items
