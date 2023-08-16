"""
Test utility to simulate a repository.
Inspired from python-tuf's repository simulator.
"""

import logging
import datetime
from typing import List, Dict, Tuple, Iterator, Optional
from urllib import parse

from securesystemslib.keys import generate_ed25519_key
from securesystemslib.signer import SSlibSigner, SSlibKey
from tuf.api.exceptions import DownloadHTTPError
from tuf.api.metadata import (
    TOP_LEVEL_ROLE_NAMES,
    TargetFile,
    Metadata,
    Targets,
    Snapshot,
    Timestamp,
    Root,
    Key,
    MetaFile
)
from tuf.api.serialization.json import JSONSerializer
from tuf.ngclient.fetcher import FetcherInterface

logger = logging.getLogger(__name__)

class RepositorySimulator(FetcherInterface):
    """Simulates a repository that can be used for testing."""

    def __init__(self) -> None:
        # other metadata is signed on-demand (when fetched) but roots must be
        # explicitly published with publish_root() which maintains this list
        self.signed_roots: List[bytes] = []

        # signers are used on-demand at fetch time to sign metadata
        # keys are roles, values are dicts of {keyid: signer}
        self.signers: Dict[str, Dict[str, SSlibSigner]] = {}

        now = datetime.datetime.utcnow()
        self.safe_expiry = now.replace(microsecond=0) + datetime.timedelta(
            days=30
        )

        self._initialize()

    @property
    def root(self) -> Root:
        """Returns root metadata"""
        return self.md_root.signed

    @property
    def timestamp(self) -> Timestamp:
        """Returns timestamp metadata"""
        return self.md_timestamp.signed

    @property
    def snapshot(self) -> Snapshot:
        """Returns snapshot metadata"""
        return self.md_snapshot.signed

    @property
    def targets(self) -> Targets:
        """Returns targets metadata"""
        return self.md_targets.signed

    def all_targets(self) -> Iterator[Tuple[str, Targets]]:
        """Yield role name and signed portion of targets one by one."""
        yield Targets.type, self.md_targets.signed

    @staticmethod
    def create_key() -> Tuple[Key, SSlibSigner]:
        """Creates ed25519 public and private keys."""
        key = generate_ed25519_key()
        return SSlibKey.from_securesystemslib_key(key), SSlibSigner(key)

    def add_signer(self, role: str, signer: SSlibSigner) -> None:
        """Adds signer to the specified role."""
        if role not in self.signers:
            self.signers[role] = {}
        self.signers[role][signer.key_dict["keyid"]] = signer

    def _initialize(self) -> None:
        """Setup a minimal valid repository"""

        # pylint: disable=attribute-defined-outside-init
        self.md_targets = Metadata(Targets(expires=self.safe_expiry))
        self.md_snapshot = Metadata(Snapshot(expires=self.safe_expiry))
        self.md_timestamp = Metadata(Timestamp(expires=self.safe_expiry))
        self.md_root = Metadata(Root(expires=self.safe_expiry))

        for role in TOP_LEVEL_ROLE_NAMES:
            key, signer = self.create_key()
            self.md_root.signed.add_key(key, role)
            self.add_signer(role, signer)

        self.publish_root()

    def publish_root(self) -> None:
        """Sign and store a new serialized version of root."""
        self.md_root.signatures.clear()
        for signer in self.signers[Root.type].values():
            self.md_root.sign(signer, append=True)

        self.signed_roots.append(self.md_root.to_bytes(JSONSerializer()))
        # logger.debug("Published root v%d", self.root.version)

    def update_timestamp(self) -> None:
        """Update timestamp and assign snapshot version to snapshot_meta
        version.
        """

        hashes = None
        length = None

        self.timestamp.snapshot_meta = MetaFile(
            self.snapshot.version, length, hashes
        )

        self.timestamp.version += 1

    def update_snapshot(self) -> None:
        """Update snapshot, assign targets versions and update timestamp."""
        for role, delegate in self.all_targets():
            hashes = None
            length = None

            self.snapshot.meta[f"{role}.json"] = MetaFile(
                delegate.version, length, hashes
            )

        self.snapshot.version += 1
        self.update_timestamp()

    def add_target(self, cid: str, data: bytes, path: str, length: int | None) -> None:
        """Create a target from data and add it to the target_files."""
        targets = self.targets

        target = TargetFile.from_data(path, data)
        # First remove any sha256 hashes
        target.hashes.clear()
        target.hashes["ipfs"] = cid
        if length is not None:
            target.length = length

        targets.targets[path] = target

    def _fetch(self, url: str) -> Iterator[bytes]:
        """Fetches data from the given url and returns an Iterator (or yields
        bytes).
        """
        path = parse.urlparse(url).path
        if path.startswith("/metadata/") and path.endswith(".json"):
            # figure out rolename and version
            ver_and_name = path[len("/metadata/") :][: -len(".json")]
            version_str, _, role = ver_and_name.partition(".")
            # root is always version-prefixed while timestamp is always NOT
            if role == Root.type or (
                self.root.consistent_snapshot and ver_and_name != Timestamp.type
            ):
                version: Optional[int] = int(version_str)
            else:
                # the file is not version-prefixed
                role = ver_and_name
                version = None

            yield self.fetch_metadata(role, version)
        else:
            raise DownloadHTTPError(f"Unknown path '{path}'", 404)

    def fetch_metadata(self, role: str, version: Optional[int] = None) -> bytes:
        """Return signed metadata for 'role', using 'version' if it is given.

        If version is None, non-versioned metadata is being requested.
        """
        # decode role for the metadata
        role = parse.unquote(role, encoding="utf-8")

        if role == Root.type:
            # return a version previously serialized in publish_root()
            if version is None or version > len(self.signed_roots):
                raise DownloadHTTPError(f"Unknown root version {version}", 404)
            logger.debug("fetched root version %d", version)
            return self.signed_roots[version - 1]

        # sign and serialize the requested metadata
        # pylint: disable=invalid-name
        md: Optional[Metadata]
        if role == Timestamp.type:
            md = self.md_timestamp
        elif role == Snapshot.type:
            md = self.md_snapshot
        elif role == Targets.type:
            md = self.md_targets

        if md is None:
            raise DownloadHTTPError(f"Unknown role {role}", 404)

        md.signatures.clear()
        for signer in self.signers[role].values():
            md.sign(signer, append=True)

        logger.debug(
            "fetched %s v%d with %d sigs",
            role,
            md.signed.version,
            len(self.signers[role]),
        )
        return md.to_bytes(JSONSerializer())
