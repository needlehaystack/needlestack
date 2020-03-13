from needlestack.servicers import factory
from needlestack.cluster_managers import ClusterManager


def test_create_zookeeper_cluster_manager(test_servicer_tls_config):
    manager = factory.create_zookeeper_cluster_manager(test_servicer_tls_config)
    assert isinstance(manager, ClusterManager)
