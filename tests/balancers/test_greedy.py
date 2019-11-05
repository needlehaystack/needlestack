from needlestack.balancers import Item, Knapsack, KnapsackState
from needlestack.balancers.greedy import GreedyAlgorithm


def test_greedy_add_one_knapsack():
    item = Item("id", "value")
    knapsack = Knapsack("id", "value")
    state = KnapsackState()
    state.add_item(item)
    state.add_knapsack(knapsack)
    algo = GreedyAlgorithm()
    algo.add([item], state)
    assert item in knapsack.items


def test_greedy_add_two_knapsack():
    items = [Item("id1", "value"), Item("id2", "value")]
    knapsacks = [Knapsack("id1", "value"), Knapsack("id2", "value")]
    state = KnapsackState()
    state.add_items(items)
    state.add_knapsacks(knapsacks)
    algo = GreedyAlgorithm()
    algo.add(items, state)
    for knapsack in knapsacks:
        assert len(knapsack.items) == 1


def test_greedy_add_item_quantity_to_much():
    item_2x = Item("id", "value", quantity=2)
    knapsack = Knapsack("id", "value")
    state = KnapsackState()
    state.add_item(item_2x)
    state.add_knapsack(knapsack)
    algo = GreedyAlgorithm()
    algo.add([item_2x], state)
    assert len(knapsack.items) == 1


def test_greedy_add_item_quantity():
    item_2x = Item("id1", "value", quantity=2)
    item_3x = Item("id2", "value", quantity=3)
    items = [item_2x, item_3x]
    knapsacks = [
        Knapsack("id1", "value"),
        Knapsack("id2", "value"),
        Knapsack("id3", "value"),
    ]
    state = KnapsackState()
    state.add_items(items)
    state.add_knapsacks(knapsacks)
    algo = GreedyAlgorithm()
    algo.add(items, state)
    for knapsack in knapsacks:
        assert item_3x in knapsack.items
