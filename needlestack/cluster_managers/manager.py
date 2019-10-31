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

    def add_collections(
        self, collections: List[collections_pb2.Collection]
    ) -> List[collections_pb2.Collection]:
        raise NotImplementedError()

    def delete_collections(self, collection_names: List[str]) -> List[str]:
        raise NotImplementedError()

    def list_nodes(self) -> List[collections_pb2.Node]:
        raise NotImplementedError()

    def list_collections(
        self, collection_names: Optional[List[str]] = None
    ) -> List[collections_pb2.Collection]:
        raise NotImplementedError()

    def list_local_collections(self) -> List[collections_pb2.Collection]:
        raise NotImplementedError()

    def get_searchers(
        self, collection_name: str, shard_names: Optional[List[str]] = None
    ) -> List[Tuple[str, List[str]]]:
        """Get all active searches for specified shards in a collection. If no shards are provided
        then return all shards.
        """
        raise NotImplementedError()
