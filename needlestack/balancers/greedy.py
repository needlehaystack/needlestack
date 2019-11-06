from needlestack.balancers import Algorithm


class GreedyAlgorithm(Algorithm):
    """Greedy algorithm that places the largest item in the lightest knapsack,
    then repeat until all items are placed somewhere."""

    def add(self, items, knapsacks):
        items = sorted(items, key=lambda x: x.weight, reverse=True)
        num_knapsacks = len(knapsacks)

        for item in items:
            knapsacks = sorted(
                knapsacks, key=lambda x: (x.current_weight, len(x.items))
            )

            quantity = (
                item.quantity if item.quantity <= num_knapsacks else num_knapsacks
            )

            for i in range(quantity):
                knapsacks[i].add_item(item)
