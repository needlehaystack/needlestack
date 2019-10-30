from typing import List, Tuple, Optional

from needlestack.apis import collections_pb2


class ClusterManager(object):
    """Maintains connection to cluster manager to keep track of other nodes"""

    def up(self):
        raise NotImplementedError()

    def down(self):
        raise NotImplementedError()

    def clean(self):
        raise NotImplementedError()

    def configure_collections(self, collections: List[collections_pb2.Collection]):
        """Configure a list of collections into Zookeeper
        """
        raise NotImplementedError()

    def get_collections_to_load(self) -> List[collections_pb2.Collection]:
        """Get a list of collections and shards to load into Searcher servicer
        """
        raise NotImplementedError()

    def get_searchers(
        self, collection_name: str, shard_names: Optional[List[str]] = None
    ) -> List[Tuple[str, List[str]]]:
        """Get all active searches for specified shards in a collection. If no shards are provided
        then return all shards.
        """
        raise NotImplementedError()

    def get_live_nodes(self) -> List[collections_pb2.Node]:
        raise NotImplementedError()

    def get_collections(
        self, collection_names: Optional[List[str]] = None
    ) -> List[collections_pb2.Collection]:
        raise NotImplementedError()
