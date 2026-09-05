"""Service topology representation for CrossFault simulator."""

from typing import List, Tuple


class ServiceTopology:
    """Represents a service-to-service communication topology."""

    def __init__(self, path: List[str]):
        if not path or len(path) < 2:
            raise ValueError("Topology path must contain at least two services to form a dependency chain.")
        self._path = list(path)

    @property
    def path(self) -> List[str]:
        return list(self._path)

    def get_hops(self) -> List[Tuple[str, str]]:
        """Returns ordered list of (source, destination) service pairs along the topology path."""
        return [
            (self._path[i], self._path[i + 1])
            for i in range(len(self._path) - 1)
        ]

    def contains_service(self, service_name: str) -> bool:
        return service_name in self._path

    def contains_hop(self, source: str, destination: str) -> bool:
        for s, d in self.get_hops():
            if s == source and d == destination:
                return True
        return False
