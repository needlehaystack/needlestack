from typing import Optional

import grpc
from grpc._channel import Channel
from grpc_health.v1.health_pb2_grpc import HealthStub

from needlestack.apis.servicers_pb2_grpc import MergerStub, SearcherStub
from needlestack.utilities.multiton import multiton_pattern


def create_channel(hostport: str, root_certificate: Optional[str] = None) -> Channel:
    if root_certificate:
        with open(root_certificate, "rb") as f:
            credentials = grpc.ssl_channel_credentials(root_certificates=f.read())
        return grpc.secure_channel(hostport, credentials)
    else:
        return grpc.insecure_channel(hostport)


def create_health_stub(
    hostport: str, root_certificate: Optional[str] = None
) -> HealthStub:
    channel = get_channel(hostport, root_certificate)
    return HealthStub(channel)


def create_merger_stub(
    hostport: str, root_certificate: Optional[str] = None
) -> MergerStub:
    channel = get_channel(hostport, root_certificate)
    return MergerStub(channel)


def create_searcher_stub(
    hostport: str, root_certificate: Optional[str] = None
) -> SearcherStub:
    channel = get_channel(hostport, root_certificate)
    return SearcherStub(channel)


get_channel = multiton_pattern(create_channel)
get_health_stub = multiton_pattern(create_health_stub)
get_merger_stub = multiton_pattern(create_merger_stub)
get_searcher_stub = multiton_pattern(create_searcher_stub)
