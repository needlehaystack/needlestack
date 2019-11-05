import logging
from copy import deepcopy
from typing import List, Set, Any, Optional, Dict

from needlestack.apis import collections_pb2
from needlestack.exceptions import KnapsackCapacityException, KnapsackItemException

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
            raise KnapsackCapacityException("Knapsack over weight capacity")
        elif item in self.items:
            raise KnapsackItemException("Item already exists in this knapsack")
        else:
            self.items.add(item)
            self.current_weight += item.weight


class KnapsackState(object):

    """Maintains the state of a knapsack solution.

    TODO: Refactor all of these to make more sense
    """

    knapsacks: List[Knapsack]
    items: List[Item]
    items_to_knapsacks: Dict[str, List[Knapsack]]

    def __init__(self):
        self.knapsacks = []
        self.items = []
        self.items_to_knapsacks = {}

    def add_knapsack(self, knapsack: Knapsack):
        self.knapsacks.append(knapsack)

    def add_knapsacks(self, knapsacks: List[Knapsack]):
        for knapsack in knapsacks:
            self.add_knapsack(knapsack)

    def add_item(self, item: Item):
        self.items.append(item)
        if item.id in self.items_to_knapsacks:
            raise KnapsackItemException(
                f"Item {item.id} already exist in KnapsackState"
            )
        else:
            self.items_to_knapsacks[item.id] = []

    def add_items(self, items: List[Item]):
        for item in items:
            self.add_item(item)

    def add_item_to_knapsack(self, knapsack, item):
        knapsack.add_item(item)
        self.items_to_knapsacks[item.id].append(knapsack)


class Algorithm(object):
    def add(self, items: List[Item], state: KnapsackState):
        raise NotImplementedError()

    def rebalance(self, state: KnapsackState):
        raise NotImplementedError()


def add(
    nodes: List[collections_pb2.Node],
    current_collections: List[collections_pb2.Collection],
    add_collections: List[collections_pb2.Collection],
    algorithm: Algorithm,
) -> List[collections_pb2.Collection]:
    state = _get_knapsack_state(nodes, current_collections)

    add_items = []
    for collection in deepcopy(add_collections):
        if collection.replication_factor > len(nodes):
            logger.warn(
                f"{collection.name}.replication_factor is {collection.replication_factor}, but only {len(nodes)} nodes."
            )
        for shard in collection.shards:
            item = Item(
                f"{collection.name}:{shard.name}",
                (collection, shard),
                collection.replication_factor,
                shard.weight or 1.0,
            )
            add_items.append(item)
            state.add_item(item)

    algorithm.add(add_items, state)

    collections = _extract_collection_proto(state)
    add_set = {collection.name for collection in add_collections}

    return [collection for collection in collections if collection.name in add_set]


def rebalance(
    nodes: List[collections_pb2.Node],
    current_collections: List[collections_pb2.Collection],
    algorithm: Algorithm,
) -> List[collections_pb2.Collection]:
    state = _get_knapsack_state(nodes, current_collections)
    algorithm.rebalance(state)
    return _extract_collection_proto(state)


def _get_knapsack_state(
    nodes: List[collections_pb2.Node], collections: List[collections_pb2.Collection]
) -> KnapsackState:
    state = KnapsackState()

    for node in deepcopy(nodes):
        knapsack = Knapsack(node.hostport, node)
        state.add_knapsack(knapsack)

    knapsacks_map = {knapsack.id: knapsack for knapsack in state.knapsacks}

    for collection in deepcopy(collections):
        for shard in collection.shards:
            item = Item(
                f"{collection.name}:{shard.name}",
                (collection, shard),
                collection.replication_factor,
                shard.weight or 1.0,
            )
            state.add_item(item)
            for replica in shard.replicas:
                knapsack = knapsacks_map[replica.node.hostport]
                state.add_item_to_knapsack(knapsack, item)
            shard.ClearField("replicas")
        collection.ClearField("shards")

    return state


def _extract_collection_proto(state: KnapsackState) -> List[collections_pb2.Collection]:
    items_map = {item.id: item for item in state.items}

    for item_id, knapsacks in state.items_to_knapsacks.items():
        item = items_map[item_id]
        collection, shard = item.value
        replicas = [
            collections_pb2.Replica(node=knapsack.value) for knapsack in knapsacks
        ]
        shard.replicas.extend(replicas)
        collection.shards.extend([shard])

    return [item.value[0] for item in state.items]
