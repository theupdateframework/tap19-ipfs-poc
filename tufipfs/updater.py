"""
The ``IpfsUpdater`` class is a subclass of the original ``Updater``
from python-tuf with IPFS functionalities.
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
    """Creates a new ``Updater`` with additional IPFS functionalities.

    Args:
        metadata_dir: Local metadata directory. Directory must be
            writable and it must contain a trusted root.json file
        metadata_base_url: Base URL for all remote metadata downloads
        gateway: URL of gateway to download IPFS files
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
        # TODO: testing required
        targetinfo.verify_length_and_hashes(target_file)
        
        # Save the target file locally
        with open(filepath, 'wb') as destination_file:
                destination_file.write(target_file)
        
        logger.debug("Downloaded target %s", targetinfo.path)
        return filepath
    
    def find_cached_target(
        self,
        targetinfo: TargetFile,
        filepath: Optional[str] = None,
    ) -> Optional[str]:
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