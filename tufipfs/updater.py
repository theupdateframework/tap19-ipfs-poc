"""
The ``IpfsUpdater`` class is a subclass of the original ``Updater`` class
of ``tuf.ngclient`` which is a client implementation built on top of
the metadata API for traditional file system. ``IpfsUpdater`` extends the
functionalities of the ``Updater`` class for IPFS targets. The client
workflow remains the same as specified in the TUF specification.

The ``IpfsUpdater`` provides different implementation specifically during
downloading of the target. When TUF is used with IPFS, it becomes redundant for
TUF to verify artifact integrity. This in fact is done implicitly while downloading
files in IPFS. Unlike traditional file system where files are associated with arbitrary
names, in IPFS files are associated with a fixed ``CID (content-based identifier)`` which
is based on the content of the file. These CIDs are based on the file's cryptographic hash.

The ``IpfsUpdater`` has an IPFS gateway property using which the IpfsUpdater makes a
call over HTTP to download files. ``IpfsUpdater`` fetches the target's CID from its
``TargetInfo``. However it is still optional to verify other hashes like sha256, etc.
"""

import logging
import os
from typing import Optional
from urllib import parse
import requests
from tuf.api.metadata import TargetFile
from tuf.ngclient import Updater
from tuf.ngclient.config import UpdaterConfig
from tuf.ngclient.fetcher import FetcherInterface
from tuf.api.exceptions import DownloadError

logger = logging.getLogger(__name__)


class IpfsUpdater(Updater):
    """Creates a new ``IpfsUpdater`` instance for IPFS based targets.

    Args:
        metadata_dir: Local metadata directory. Directory must be
            writable and it must contain a trusted root.json file
        metadata_base_url: Base URL for all remote metadata downloads
        gateway: URL of IPFS gateway to download target files
        target_dir: Local targets directory. Directory must be writable. It
            will be used as the default target download directory by
            ``find_cached_target()`` and ``download_target()``
        target_base_url: ``Optional``; Default base URL for all remote target
            downloads. Can be individually set in ``download_target()``
        fetcher: ``Optional``; ``FetcherInterface`` implementation used to
            download both metadata and targets. Default is ``RequestsFetcher``
        config: ``Optional``; ``UpdaterConfig`` could be used to setup common
            configuration options.
    """

    def __init__(
        self,
        metadata_dir: str,
        metadata_base_url: str,
        gateway: str,
        target_dir: Optional[str] = None,
        target_base_url: Optional[str] = None,
        fetcher: Optional[FetcherInterface] = None,
        config: Optional[UpdaterConfig] = None,
    ):
        super().__init__(
            metadata_dir,
            metadata_base_url,
            target_dir,
            target_base_url,
            fetcher,
            config,
        )
        self.gateway = gateway
        if target_base_url is None:
            self._target_base_url = None
        else:
            self._target_base_url = _ensure_trailing_slash(target_base_url)

    def download_target(
        self,
        targetinfo: TargetFile,
        filepath: Optional[str] = None,
        target_base_url: Optional[str] = None,
    ) -> str:
        """Download the target file specified by ``targetinfo`` using IPFS gateway.
        Args:
            targetinfo: ``TargetFile`` from ``get_targetinfo()``.
            filepath: Local path to download into. If ``None``, the file is
                downloaded into directory defined by ``target_dir`` constructor
                argument using a generated filename. If file already exists,
                it is overwritten.
            target_base_url: Base URL used to form the final target
                download URL. Default is the value provided in ``Updater()``

        Returns:
            Local path to downloaded file
        """

        if filepath is None:
            filepath = super()._generate_target_file_path(targetinfo)

        if target_base_url is None:
            if self._target_base_url is None:
                raise ValueError(
                    "target_base_url must be set in either "
                    "download_target() or constructor"
                )

            target_base_url = self._target_base_url
        else:
            target_base_url = _ensure_trailing_slash(target_base_url)

        hashes = targetinfo.hashes
        # Check if CID exists
        if hashes.get("ipfs") is None:
            raise ValueError("CID missing from hashes")

        # Download the target file using gateway
        cid = hashes.pop("ipfs")
        file_url = _ensure_trailing_slash(self.gateway) + "ipfs/" + cid
        response = requests.get(file_url, timeout=5)
        if response.status_code != 200:
            raise DownloadError(f"Unable to download target using url {file_url}")

        target_file = response.content
        targetinfo.verify_length_and_hashes(target_file)

        # Save the target file locally
        with open(filepath, "wb") as destination_file:
            destination_file.write(target_file)

        logger.debug("Downloaded target %s", targetinfo.path)
        return filepath

    def find_cached_target(
        self,
        targetinfo: TargetFile,
        filepath: Optional[str] = None,
    ) -> Optional[str]:
        """Check whether the file already exists locally.

        Args:
            targetinfo: ``TargetFile`` from ``get_targetinfo()``.
            filepath: Local path to file. If ``None``, a file path is
                generated based on ``target_dir`` constructor argument.

        Returns:
            Local file path if the file is an up to date target file.
            ``None`` if file is not found or it is not up to date.
        """

        if filepath is None:
            filepath = self._generate_target_file_path(targetinfo)

        if os.path.exists(filepath):
            return filepath

        return None

    def _generate_target_file_path(self, targetinfo: TargetFile) -> str:
        if self.target_dir is None:
            raise ValueError("target_dir must be set if filepath is not given")

        # Use URL encoded target path as filename
        filename = parse.quote(targetinfo.path, "")
        return os.path.join(self.target_dir, filename)


def _ensure_trailing_slash(url: str) -> str:
    """Return url guaranteed to end in a slash."""
    return url if url.endswith("/") else f"{url}/"
