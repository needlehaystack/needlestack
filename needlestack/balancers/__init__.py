import logging
from typing import Callable, List, Set, Any, Optional, Dict

from needlestack.apis import collections_pb2

logger = logging.getLogger("needlestack")


class Item(object):
    """Item that goes into a knapsack

    Attributes:
        id: ID for item
        value: Value the item is representing
        quantity: How many of these item should exist
        weight: How much this item weighs
    """

    id: str
    value: Any
    quantity: int
    weight: float

    def __init__(self, id, value, quantity: int = 1, weight: float = 0.0):
        self.id = id
        self.value = value
        self.quantity = quantity
        self.weight = weight


class Knapsack(object):
    """Knapsack that can hold multiple items

    Attributes:
        id: ID for knapsack
        value: Value this knapsack is representing
        items: Set of items in knapsack
        current_weight: Current weight in the knapsack
        capacity: Max weight for knapsack
    """

    id: str
    value: Any
    items: Set[Item]
    current_weight: float
    capacity: Optional[float] = None

    def __init__(self, id, value):
        self.id = id
        self.value = value
        self.items = set()
        self.current_weight = 0

    def add_item(self, item: Item):
        if self.capacity and (self.current_weight + item.weight) > self.capacity:
            raise ValueError("Knapsack over weight capacity")
        if item in self.items:
            raise ValueError("Item already exists in this knapsack")
        else:
            self.items.add(item)
            self.current_weight += item.weight


def balance(
    collections: List[collections_pb2.Collection],
    nodes: List[collections_pb2.Node],
    solver: Callable[[List[Item], List[Knapsack]], None],
):
    """Function that takes colletion protobufs, node protobufs, and a function to
    solve the knapsack problem. This will mutate the collection protobufs to assign
    each shard to live on specific nodes.

    Args:
        collections: List of collections to load on cluster
        nodes: List of nodes that exists on cluster
        solver: Function to solve the knapsack problem
    """
    items = []
    for collection in collections:
        if collection.replication_factor > len(nodes):
            logger.warn(
                f"{collection.name}.replication_factor is {collection.replication_factor}, but only {len(nodes)} nodes."
            )
        for shard in collection.shards:
            item = Item(
                f"{collection.name}:{shard.name}",
                shard,
                collection.replication_factor,
                shard.weight or 1.0,
            )
            items.append(item)

    knapsacks = [Knapsack(node.hostport, node) for node in nodes]

    solver(items, knapsacks)

    shard_to_nodes: Dict[str, List[collections_pb2.Node]] = {}
    for knapsack in knapsacks:
        for item in knapsack.items:
            shard_to_nodes[item.id] = shard_to_nodes.get(item.id, [])
            shard_to_nodes[item.id].append(knapsack.value)

    for collection in collections:
        for shard in collection.shards:
            shard_nodes = shard_to_nodes[f"{collection.name}:{shard.name}"]
            shard.replicas.extend(shard_nodes)
