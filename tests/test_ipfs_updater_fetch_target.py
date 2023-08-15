"""
Test 'fetch target' of IpfsUpdater as well as simulating
a basic repository from uploading metadatas to adding targets
"""

import sys
sys.path.append(".")
import os
import tempfile
import unittest
from dataclasses import dataclass
from repository_simulator import RepositorySimulator
from utils import DataSet, run_sub_tests_with_dataset
from tufipfs.updater import IpfsUpdater

@dataclass
class TestTarget:
    """Sample targets for testing"""
    path: str
    content: bytes
    cid: str

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

    targets: DataSet = {
        "text": TestTarget(
            path="file.txt",
            content=b"file 1 content",
            cid="QmSFEbC6Y17cdti7damkjoqESWftkyfSXjdKDQqnf4ECV7"
        ),
    }

    @run_sub_tests_with_dataset(targets)
    def test_fetch_target(self, target: TestTarget) -> None:
        """Tests the download functionality of IpfsUpdater"""
        # Add targets to repository
        self.sim.targets.version += 1
        self.sim.add_target(target.cid, target.content, target.path)
        self.sim.update_snapshot()

        path = os.path.join(self.targets_dir, target.path)

        # Initialize IpfsUpdater with private gateway
        private_gateway = "http://127.0.0.1:8081"
        updater = self._init_updater(private_gateway)
        info = updater.get_targetinfo(target.path)
        assert info is not None
        self.assertEqual(path, updater.download_target(info))

        # Initialize IpfsUpdater with public gateway
        public_gateway = "https://ipfs.io"
        updater = self._init_updater(public_gateway)
        info = updater.get_targetinfo(target.path)
        assert info is not None
        self.assertEqual(path, updater.download_target(info))


if __name__ == "__main__":
    unittest.main()
