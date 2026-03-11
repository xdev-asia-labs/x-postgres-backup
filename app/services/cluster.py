"""Service to interact with Patroni REST API and get cluster status."""

import logging
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    name: str
    host: str
    role: str  # leader, replica, sync_standby
    state: str  # running, streaming, stopped
    timeline: int = 0
    lag: int = 0
    patroni_url: str = ""


@dataclass
class ClusterStatus:
    name: str = ""
    nodes: list[NodeInfo] = field(default_factory=list)
    leader: NodeInfo | None = None
    healthy: bool = False
    error: str | None = None


async def get_cluster_status() -> ClusterStatus:
    """Query Patroni REST API on all nodes to build cluster status."""
    status = ClusterStatus()

    for node_endpoint in settings.PATRONI_NODES:
        url = f"http://{node_endpoint}/cluster"
        try:
            auth = None
            if settings.PATRONI_AUTH_ENABLED:
                auth = (settings.PATRONI_AUTH_USERNAME, settings.PATRONI_AUTH_PASSWORD)

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, auth=auth)
                if resp.status_code == 200:
                    data = resp.json()
                    status.name = data.get("scope", "unknown")
                    for member in data.get("members", []):
                        node = NodeInfo(
                            name=member.get("name", ""),
                            host=member.get("host", "").split(":")[0],
                            role=member.get("role", "unknown"),
                            state=member.get("state", "unknown"),
                            timeline=member.get("timeline", 0),
                            lag=member.get("lag", 0),
                            patroni_url=member.get("api_url", ""),
                        )
                        status.nodes.append(node)
                        if node.role in ("leader", "master"):
                            status.leader = node
                    status.healthy = any(
                        n.role in ("leader", "master") and n.state == "running"
                        for n in status.nodes
                    )
                    return status
        except Exception as e:
            logger.warning("Failed to reach Patroni at %s: %s", url, e)
            continue

    status.error = "Could not reach any Patroni node"
    return status


async def get_node_health(host: str, port: int = 8008) -> dict:
    """Get health of a specific node."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://{host}:{port}/health")
            return {"status": resp.status_code, "data": resp.json()}
    except Exception as e:
        return {"status": 0, "error": str(e)}


async def get_databases() -> list[str]:
    """Get list of user databases from leader node via Patroni."""
    status = await get_cluster_status()
    if not status.leader:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            auth = None
            if settings.PATRONI_AUTH_ENABLED:
                auth = (settings.PATRONI_AUTH_USERNAME, settings.PATRONI_AUTH_PASSWORD)
            resp = await client.get(
                f"http://{status.leader.host}:{settings.PATRONI_NODES[0].split(':')[1]}/patroni",
                auth=auth,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("database", {}).get("databases", [])
    except Exception:
        pass

    return []
