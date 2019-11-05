from needlestack.balancers import Algorithm


class GreedyAlgorithm(Algorithm):
    def add(self, items, state):
        """A greedy algorithm that places the largest items first.
        From heaviest to lightest, each item is placed in the lightest
        knapsack.
        """
        items = sorted(items, key=lambda x: x.weight, reverse=True)
        num_knapsacks = len(state.knapsacks)

        for item in items:
            knapsacks = sorted(
                state.knapsacks, key=lambda x: (x.current_weight, len(x.items))
            )

            quantity = (
                item.quantity if item.quantity <= num_knapsacks else num_knapsacks
            )

            for i in range(quantity):
                state.add_item_to_knapsack(knapsacks[i], item)
