import threading
from typing import Dict, Union, Callable, Optional

import grpc
from grpc._channel import Channel
from grpc_health.v1.health_pb2_grpc import HealthStub

from needlestack.apis.servicers_pb2_grpc import MergerStub, SearcherStub


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


def singleton_getter(
    create_fn: Callable[
        [str, Optional[str]], Union[Channel, HealthStub, MergerStub, SearcherStub]
    ]
) -> Callable[
    [str, Optional[str]], Union[Channel, HealthStub, MergerStub, SearcherStub]
]:
    lock = threading.Lock()
    cache: Dict[str, Union[Channel, HealthStub, MergerStub, SearcherStub]] = {}

    def getter(
        hostport: str, root_certificate: Optional[str] = None
    ) -> Union[Channel, HealthStub, MergerStub, SearcherStub]:
        key = f"{hostport}|{root_certificate}"
        if key in cache:
            return cache[key]
        else:
            obj = create_fn(hostport, root_certificate)
            with lock:
                cache[key] = obj
            return obj

    return getter


get_channel = singleton_getter(create_channel)
get_health_stub = singleton_getter(create_health_stub)
get_merger_stub = singleton_getter(create_merger_stub)
get_searcher_stub = singleton_getter(create_searcher_stub)
