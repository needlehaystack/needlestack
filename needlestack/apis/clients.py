from typing import Dict

import grpc
from grpc._channel import Channel

from needlestack.apis.servicers_pb2_grpc import MergerStub, SearcherStub
from needlestack.apis.health_pb2_grpc import HealthStub

CHANNELS: Dict[str, Channel] = {}
HEALTH_STUBS: Dict[str, HealthStub] = {}
MERGER_STUBS: Dict[str, MergerStub] = {}
SEARCHER_STUBS: Dict[str, SearcherStub] = {}


def create_channel(hostport: str) -> Channel:
    return grpc.insecure_channel(hostport)


def create_health_stub(hostport: str) -> HealthStub:
    channel = get_channel(hostport)
    return HealthStub(channel)


def create_merger_stub(hostport: str) -> MergerStub:
    channel = get_channel(hostport)
    return MergerStub(channel)


def create_searcher_stub(hostport: str) -> SearcherStub:
    channel = get_channel(hostport)
    return SearcherStub(channel)


def get_channel(hostport: str) -> Channel:
    if hostport in CHANNELS:
        return CHANNELS[hostport]
    else:
        channel = create_channel(hostport)
        CHANNELS[hostport] = channel
        return channel


def get_health_stub(hostport: str) -> HealthStub:
    if hostport in HEALTH_STUBS:
        return HEALTH_STUBS[hostport]
    else:
        stub = create_health_stub(hostport)
        HEALTH_STUBS[hostport] = stub
        return stub


def get_merger_stub(hostport: str) -> MergerStub:
    if hostport in MERGER_STUBS:
        return MERGER_STUBS[hostport]
    else:
        stub = create_merger_stub(hostport)
        MERGER_STUBS[hostport] = stub
        return stub


def get_searcher_stub(hostport: str) -> SearcherStub:
    if hostport in SEARCHER_STUBS:
        return SEARCHER_STUBS[hostport]
    else:
        stub = create_searcher_stub(hostport)
        SEARCHER_STUBS[hostport] = stub
        return stub
