import asyncio
from typing import List, Optional, Dict, Union
from ..base import A0G

try:
    import qdrant_client
    from qdrant_client.models import PointStruct, VectorParams, AsyncQdrantClient
except ImportError:
    print("qdrant-client is required. Install with: pip install python-0g[qdrant]")


class DQDrant:
    """
    Distributed Qdrant client that integrates with 0G storage network.
    Uses a single collection across multiple Qdrant instances.
    Loaded clients are read-only, active client is read-write.
    """

    def __init__(self, a0g: A0G, collection_name: str, vectors_config: Union["VectorParams", Dict]):
        self.a0g = a0g
        self.collection_name = collection_name

        # Convert dict to VectorParams if needed
        if isinstance(vectors_config, dict):
            self.vectors_config = VectorParams(**vectors_config)
        else:
            self.vectors_config = vectors_config

        # Loaded clients (read-only from 0G storage)
        self.loaded_clients: List[qdrant_client.AsyncQdrantClient] = []
        self.loaded_snapshots: List[Dict] = []  # Metadata about loaded snapshots

        # Active client (read-write, for new data)
        self.active_client = AsyncQdrantClient(":memory:")
        self._active_client_initialized = False

    async def _ensure_active_collection(self):
        """Ensure active client has the collection created"""
        if not self._active_client_initialized:
            try:
                await self.active_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=self.vectors_config
                )
                self._active_client_initialized = True
                print(f"Initialized active collection '{self.collection_name}'")
            except Exception as e:
                if "already exists" in str(e).lower():
                    self._active_client_initialized = True
                else:
                    raise e

    # async def load(self, path: Path):
    #     """
    #     Load snapshot manifests from 0G storage using JSON metadata file.
    #
    #     Args:
    #         path: Path to JSON file containing snapshot information
    #     """
    #     from qdrant_client import AsyncQdrantClient
    #
    #     if not path.exists():
    #         return
    #
    #     # Read JSON metadata
    #     with path.open("r", encoding="utf-8") as f:
    #         snapshots = json.load(f)
    #
    #     print(f"Loading {len(snapshots)} snapshots from 0G storage...")
    #
    #     # Process each snapshot
    #     for i, snapshot_info in enumerate(snapshots):
    #         root_hash = snapshot_info["root_hash"]
    #         print(f"Loading snapshot {i+1}: {root_hash}")
    #
    #         with tempfile.TemporaryDirectory() as temp_dir:
    #             snapshot_path = Path(temp_dir) / f"snapshot_{i}"
    #             self.a0g.download_from_storage(
    #                 ZGStorageObject(root_hash=root_hash, tx_hash=""),
    #                 path=snapshot_path
    #             )
    #
    #             client = AsyncQdrantClient(":memory:")
    #             await client.create_collection(
    #                 collection_name=self.collection_name,
    #                 vectors_config=self.vectors_config
    #             )
    #             await client.recover_snapshot(self.collection_name,
    #                                           location=snapshot_path.absolute().as_uri())
    #             self.loaded_clients.append(client)
    #
    #     print(f"Loaded {len(self.loaded_clients)} snapshots")
    #
    # async def dump(self, output_path: Path):
    #     """
    #     Create snapshot of active client and save to 0G storage.
    #
    #     Args:
    #         output_path: Path where to save the snapshots metadata JSON file
    #     """
    #     if not self._active_client_initialized:
    #         return
    #
    #     snapshot_info = await self.active_client.create_snapshot(
    #         collection_name=self.collection_name
    #     )
    #
    #     storage_obj = self.a0g.upload_to_storage(snapshot_info.name)
    #
    #     # Save snapshot to temp file and upload to 0G
    #     with tempfile.NamedTemporaryFile(suffix=f"_{snapshot_info.name}.snapshot", delete=False) as temp_file:
    #         temp_file.write(snapshot_data)
    #         temp_file_path = Path(temp_file.name)
    #
    #     try:
    #         # Upload snapshot file to 0G storage
    #         storage_obj = self.a0g.upload_to_storage(temp_file_path)
    #
    #         # Load or create metadata
    #         existing_data = {"snapshots": []}
    #         if output_path.exists():
    #             with output_path.open("r", encoding="utf-8") as f:
    #                 existing_data = json.load(f)
    #
    #         # Add new snapshot
    #         points_count = await self.count_points()
    #         new_snapshot = {
    #             "root_hash": storage_obj.root_hash,
    #             "tx_hash": storage_obj.tx_hash if hasattr(storage_obj, 'tx_hash') else "",
    #             "timestamp": asyncio.get_event_loop().time(),
    #             "collection_name": self.collection_name,
    #             "snapshot_name": snapshot_info.name,
    #             "points_count": points_count
    #         }
    #
    #         existing_data["snapshots"].append(new_snapshot)
    #
    #         # Save metadata JSON
    #         with output_path.open("w", encoding="utf-8") as f:
    #             json.dump(existing_data, f, indent=2, ensure_ascii=False)
    #
    #         print(f"Saved snapshot {snapshot_info.name} to 0G with hash {storage_obj.root_hash}")
    #
    #     finally:
    #         # Clean up temp file
    #         temp_file_path.unlink(missing_ok=True)
    #
    #     # Cleanup old snapshots (keep latest 2)
    #     snapshots_list = await self.active_client.list_snapshots(self.collection_name)
    #     if len(snapshots_list) > 2:
    #         old_snapshots = snapshots_list[:-2]  # All except last 2
    #         for old_snapshot in old_snapshots:
    #             await self.active_client.delete_snapshot(
    #                 collection_name=self.collection_name,
    #                 snapshot_name=old_snapshot.name
    #             )
    #             print(f"Deleted old snapshot: {old_snapshot.name}")

    async def upsert(self, points: List["PointStruct"]):
        """
        Upsert points to the active collection only (loaded clients are read-only).

        Args:
            points: List of points to upsert
        """
        await self._ensure_active_collection()

        try:
            result = await self.active_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return result
        except Exception as e:
            print(f"Failed to upsert points to collection '{self.collection_name}': {e}")
            raise

    async def search(self,
                     query_vector: Union[List[float], str],
                     limit: int = 10,
                     score_threshold: Optional[float] = None,
                     search_params: Optional[Dict] = None):
        """
        Search across loaded clients (read-only) and active client, aggregate results.
        """
        # Get all available clients
        all_clients = self.loaded_clients.copy()
        if self._active_client_initialized:
            all_clients.append(self.active_client)

        if not all_clients:
            return []

        results_lists = await asyncio.gather(*[
            client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                **(search_params or {})
            )
            for client in all_clients
        ])
        all_results = [point for result_list in results_lists for point in result_list]
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:limit]

    async def count_points(self) -> int:
        """Count total points across all clients."""
        clients_to_count = self.loaded_clients.copy()
        if self._active_client_initialized:
            clients_to_count.append(self.active_client)

        if not clients_to_count:
            return 0

        # Get collection info from all clients
        infos = await asyncio.gather(
            *[client.get_collection(self.collection_name) for client in clients_to_count],
            return_exceptions=True
        )

        total_count = 0
        for info in infos:
            if not isinstance(info, Exception):
                total_count += info.points_count

        return total_count

    def get_client_count(self) -> int:
        """Get total number of clients (loaded + active)."""
        return len(self.loaded_clients) + (1 if self._active_client_initialized else 0)

    def get_snapshots_info(self) -> List[Dict]:
        """Get information about loaded snapshots."""
        return self.loaded_snapshots.copy()

    async def clear_active_collection(self):
        """Clear all points from active collection."""
        if not self._active_client_initialized:
            return

        try:
            await self.active_client.delete_collection(self.collection_name)
            self._active_client_initialized = False
            print(f"Cleared active collection '{self.collection_name}'")
        except Exception as e:
            print(f"Failed to clear active collection: {e}")

    def get_collection_name(self) -> str:
        """Get the collection name."""
        return self.collection_name
