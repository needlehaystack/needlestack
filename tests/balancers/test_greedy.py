from needlestack.apis import collections_pb2
from needlestack.balancers import Item, Knapsack
from needlestack.balancers.greedy import GreedyAlgorithm


def test_greedy_add_one_knapsack():
    shard = collections_pb2.Shard()
    collection = collections_pb2.Collection()
    node = collections_pb2.Node()

    item = Item(collection, shard)
    knapsack = Knapsack(node)

    algo = GreedyAlgorithm()
    algo.add([item], [knapsack])
    assert item in knapsack.items


def test_greedy_add_two_knapsack():
    collection = collections_pb2.Collection()
    shard1 = collections_pb2.Shard()
    shard2 = collections_pb2.Shard()
    node1 = collections_pb2.Node()
    node2 = collections_pb2.Node()

    items = [Item(collection, shard1), Item(collection, shard2)]
    knapsacks = [Knapsack(node1), Knapsack(node2)]

    algo = GreedyAlgorithm()
    algo.add(items, knapsacks)
    for knapsack in knapsacks:
        assert len(knapsack.items) == 1


def test_greedy_add_item_quantity_to_much():
    collection = collections_pb2.Collection(replication_factor=2)
    shard = collections_pb2.Shard()
    node = collections_pb2.Node()

    item_2x = Item(collection, shard)
    knapsack = Knapsack(node)

    algo = GreedyAlgorithm()
    algo.add([item_2x], [knapsack])
    assert len(knapsack.items) == 1


def test_greedy_add_item_quantity():
    collection2 = collections_pb2.Collection(replication_factor=2)
    collection3 = collections_pb2.Collection(replication_factor=3)
    shard2 = collections_pb2.Shard()
    shard3 = collections_pb2.Shard()

    item_2x = Item(collection2, shard2)
    item_3x = Item(collection3, shard3)

    items = [item_2x, item_3x]
    knapsacks = [
        Knapsack(collections_pb2.Node()),
        Knapsack(collections_pb2.Node()),
        Knapsack(collections_pb2.Node()),
    ]

    algo = GreedyAlgorithm()
    algo.add(items, knapsacks)
    for knapsack in knapsacks:
        assert item_3x in knapsack.items

    count = 0
    for knapsack in knapsacks:
        if item_2x in knapsack.items:
            count += 1
    assert count == 2
