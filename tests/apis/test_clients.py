from needlestack.apis import clients
from needlestack.apis.servicers_pb2_grpc import MergerStub, SearcherStub
from needlestack.apis.health_pb2_grpc import HealthStub


def test_clients_stub_creaters():
    hostport = "localhost:50051"
    assert isinstance(clients.create_health_stub(hostport), HealthStub)
    assert isinstance(clients.create_merger_stub(hostport), MergerStub)
    assert isinstance(clients.create_searcher_stub(hostport), SearcherStub)


def test_clients_factory():
    hostport_a = "localhost:50051"
    hostport_b = "localhost:50052"
    assert clients.get_channel(hostport_a) == clients.get_channel(hostport_a)
    assert clients.get_health_stub(hostport_a) == clients.get_health_stub(hostport_a)
    assert clients.get_merger_stub(hostport_a) == clients.get_merger_stub(hostport_a)
    assert clients.get_searcher_stub(hostport_a) == clients.get_searcher_stub(
        hostport_a
    )
    assert clients.get_channel(hostport_a) != clients.get_channel(hostport_b)
    assert clients.get_health_stub(hostport_a) != clients.get_health_stub(hostport_b)
    assert clients.get_merger_stub(hostport_a) != clients.get_merger_stub(hostport_b)
    assert clients.get_searcher_stub(hostport_a) != clients.get_searcher_stub(
        hostport_b
    )
