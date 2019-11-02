from typing import List, Tuple, Optional

from needlestack.apis import collections_pb2


class ClusterManager(object):
    """Maintains connection to cluster manager to keep track of other nodes"""

    ACTIVE = b"ACTIVE"
    DOWN = b"DOWN"
    BOOTING = b"BOOTING"
    RECOVERING = b"RECOVERING"

    @classmethod
    def state_to_enum(cls, state):
        return {
            cls.ACTIVE: collections_pb2.Node.ACTIVE,
            cls.DOWN: collections_pb2.Node.DOWN,
            cls.BOOTING: collections_pb2.Node.BOOTING,
            cls.RECOVERING: collections_pb2.Node.RECOVERING,
        }.get(state)

    def startup(self):
        raise NotImplementedError()

    def shutdown(self):
        raise NotImplementedError()

    def cleanup(self):
        raise NotImplementedError()

    def connect_searcher(self):
        raise NotImplementedError()

    def set_state(
        self,
        state: collections_pb2.Node.State,
        collection_name: Optional[str] = None,
        shard_name: Optional[str] = None,
        hostport: Optional[str] = None,
    ):
        """Set the state of replica nodes """
        raise NotImplementedError()

    def set_local_state(
        self,
        state: collections_pb2.Node.State,
        collection_name: Optional[str] = None,
        shard_name: Optional[str] = None,
    ):
        """Set the state of replica nodes """
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
