import pytest

from needlestack.apis import collections_pb2
from needlestack.balancers.knapsack import Item, Knapsack
from needlestack.exceptions import KnapsackItemException


def test_knapsack_add_item():
    shard = collections_pb2.Shard(weight=3.14)
    collection = collections_pb2.Collection(shards=[shard])
    node = collections_pb2.Node()
    item = Item(collection, shard)
    knapsack = Knapsack(node)

    knapsack.add_item(item)
    assert item in knapsack.items
    assert knapsack.current_weight == pytest.approx(3.14)


def test_knapsack_add_duplicate_item():
    shard = collections_pb2.Shard(weight=1.12)
    collection = collections_pb2.Collection(shards=[shard])
    node = collections_pb2.Node()
    item = Item(collection, shard)
    knapsack = Knapsack(node)

    knapsack.add_item(item)
    with pytest.raises(KnapsackItemException) as excinfo:
        knapsack.add_item(item)
        assert "Item already exists in this knapsack" == str(excinfo.value)
