"""
Test 'fetch target' of IpfsUpdater as well as simulating
a basic repository from uploading metadatas to adding targets
"""

import os
import tempfile
import unittest
from repository_simulator import RepositorySimulator
from utils import run_sub_tests_with_test_files
from tufipfs.updater import IpfsUpdater

class TestFetchTarget(unittest.TestCase):
    """Test IpfsUpdater downloading target files"""
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.metadata_dir = os.path.join(self.temp_dir.name, "metadata")
        self.targets_dir = os.path.join(self.temp_dir.name, "targets")
        os.mkdir(self.metadata_dir)
        os.mkdir(self.targets_dir)

        # Setup the repository, bootstrap client root.json
        self.sim = RepositorySimulator()
        with open(os.path.join(self.metadata_dir, "root.json"), "bw") as file:
            file.write(self.sim.signed_roots[0])

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _init_updater(self, gateway: str) -> IpfsUpdater:
        """Creates a new Ipfs Updater instance."""
        updater = IpfsUpdater(
            metadata_dir=self.metadata_dir,
            metadata_base_url="https://example.com/metadata/",
            gateway=gateway,
            target_base_url="https://example.com/targets/",
            target_dir=self.targets_dir,
            fetcher=self.sim
        )
        return updater

    @run_sub_tests_with_test_files()
    def test_fetch_target(self, cid: str, file_path: str, file_bytes: bytes) -> None:
        """Tests the download functionality of IpfsUpdater"""
        private_gateway = "http://127.0.0.1:8080"
        # Add targets to repository
        self.sim.targets.version += 1
        self.sim.add_target(cid, file_path, file_bytes)
        self.sim.update_snapshot()

        destination_path = os.path.join(self.targets_dir, file_path)

        updater = self._init_updater(private_gateway)
        info = updater.get_targetinfo(file_path)
        assert info is not None
        self.assertEqual(destination_path, updater.download_target(info))

if __name__ == "__main__":
    unittest.main()
