import logging
from copy import deepcopy
from typing import List, Set, Optional, Dict

from needlestack.apis import collections_pb2
from needlestack.exceptions import KnapsackCapacityException, KnapsackItemException

logger = logging.getLogger("needlestack")


class Item(object):
    """Item that goes into a knapsack

    Attributes:
        id: ID for item
        collection:
        shard:
        quantity: How many of these item should exist
        weight: How much this item weighs
    """

    collection: collections_pb2.Collection
    shard: collections_pb2.Shard

    def __init__(
        self, collection: collections_pb2.Collection, shard: collections_pb2.Shard
    ):
        self.collection = collection
        self.shard = shard

    @property
    def id(self):
        return f"{self.collection.name}:{self.shard.name}"

    @property
    def quantity(self):
        return self.collection.replication_factor or 1

    @property
    def weight(self):
        return self.shard.weight

    def __hash__(self):
        return hash(self.id)


class Knapsack(object):
    """Knapsack that can hold multiple items

    Attributes:
        id: ID for knapsack
        node: Value this knapsack is representing
        items: Set of items in knapsack
        current_weight: Current weight in the knapsack
        capacity: Max weight for knapsack
    """

    node: collections_pb2.Node
    items: Set[Item]
    current_weight: float
    capacity: Optional[float] = None

    def __init__(self, node, capacity: Optional[float] = None):
        self.node = node
        self.capacity = capacity
        self.items = set()
        self.current_weight = 0

    @property
    def id(self):
        return self.node.hostport

    def add_item(self, item: Item):
        if self.capacity and (self.current_weight + item.weight) > self.capacity:
            raise KnapsackCapacityException("Knapsack over weight capacity")
        elif item in self.items:
            raise KnapsackItemException("Item already exists in this knapsack")
        else:
            self.items.add(item)
            self.current_weight += item.weight

    def __hash__(self):
        return hash(self.id)


class Algorithm(object):
    """Superclass for algorithm to place items in knapsacks"""

    def add(self, items: List[Item], knapsacks: List[Knapsack]):
        raise NotImplementedError()

    def rebalance(self, knapsacks: List[Knapsack]):
        raise NotImplementedError()


def calculate_add(
    nodes: List[collections_pb2.Node],
    current_collections: List[collections_pb2.Collection],
    add_collections: List[collections_pb2.Collection],
    algorithm: Algorithm,
) -> List[collections_pb2.Collection]:
    """Determine how to add a set of collections to an existing set of collections."""
    current_collections = deepcopy(current_collections)
    add_collections = deepcopy(add_collections)

    current_knapsacks = _collections_to_knapsacks(nodes, current_collections)

    new_items = []
    for collection in add_collections:
        if collection.replication_factor > len(nodes):
            logger.warn(
                f"{collection.name}.replication_factor is {collection.replication_factor}, but only {len(nodes)} nodes."
            )
        for shard in collection.shards:
            item = Item(collection, shard)
            new_items.append(item)

    algorithm.add(new_items, current_knapsacks)

    collections = _knapsacks_to_collections(current_knapsacks)
    add_set = {collection.name for collection in add_collections}

    return [collection for collection in collections if collection.name in add_set]


def calculate_rebalance(
    nodes: List[collections_pb2.Node],
    current_collections: List[collections_pb2.Collection],
    algorithm: Algorithm,
) -> List[collections_pb2.Collection]:
    current_knapsacks = _collections_to_knapsacks(nodes, current_collections)
    algorithm.rebalance(current_knapsacks)
    return _knapsacks_to_collections(current_knapsacks)


def _collections_to_knapsacks(
    nodes: List[collections_pb2.Node], collections: List[collections_pb2.Collection]
) -> List[Knapsack]:
    """A helper function to take a list of collections and convert items to knapsacks"""

    knapsacks_map = {node.hostport: Knapsack(node) for node in nodes}

    for collection in collections:
        for shard in collection.shards:
            item = Item(collection, shard)
            for replica in shard.replicas:
                knapsack = knapsacks_map[replica.node.hostport]
                knapsack.add_item(item)

    return list(knapsacks_map.values())


def _knapsacks_to_collections(
    knapsacks: List[Knapsack],
) -> List[collections_pb2.Collection]:
    """A helper function to take knapsacks filled with items and convert it a list of collections.

    TODO: The mutation by accessing the collections and shards directly in the Items gets confusing.
    Find a way to make this function more pure.
    """

    items_to_knapsacks: Dict[Item, List[Knapsack]] = {}
    for knapsack in knapsacks:
        for item in knapsack.items:
            items_to_knapsacks[item] = items_to_knapsacks.get(item, [])
            items_to_knapsacks[item].append(knapsack)

    collections_map = {}
    for item in items_to_knapsacks.keys():
        item.shard.ClearField("replicas")
        item.collection.ClearField("shards")
        collections_map[item.collection.name] = item.collection

    for item, knapsacks in items_to_knapsacks.items():
        replicas = [
            collections_pb2.Replica(node=knapsack.node) for knapsack in knapsacks
        ]
        item.shard.replicas.extend(replicas)
        item.collection.shards.extend([item.shard])

    return list(collections_map.values())
