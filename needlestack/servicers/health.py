from needlestack.apis import health_pb2
from needlestack.apis import health_pb2_grpc


class HealthServicer(health_pb2_grpc.HealthServicer):
    """Servicer to indice the status of the gRPC server

    Attributes:
        status: Enum for current status of the server
    """

    status: int

    def __init__(self):
        self.status = health_pb2.HealthCheckResponse.SERVING

    def Check(self, request, context):
        """Get the status of the gRPC server"""
        return health_pb2.HealthCheckResponse(status=self.status)
