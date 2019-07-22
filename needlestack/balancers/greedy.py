from typing import List

from needlestack.balancers import Item, Knapsack


def solver(items: List[Item], knapsacks: List[Knapsack]):
    """A greedy algorithm that places the largest items first.
    From heaviest to lightest, each item is placed in the lightest
    knapsack.
    """
    items = sorted(items, key=lambda x: x.weight, reverse=True)

    for item in items:
        knapsacks = sorted(knapsacks, key=lambda x: (x.current_weight, len(x.items)))

        num_knapsacks = len(knapsacks)
        if item.quantity > num_knapsacks:
            quantity = num_knapsacks
        else:
            quantity = item.quantity

        for i in range(quantity):
            knapsacks[i].add_item(item)
