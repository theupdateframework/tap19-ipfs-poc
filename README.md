# <img src="https://i.imgur.com/eSeNsYf.png">

This repository serves the purpose of **Proof-of-Concept** implementation for [**TAP 19**](https://github.com/theupdateframework/taps/blob/master/tap19.md). The TAP explores how TUF can be adapted to content addressed ecosystems that have in-built integrity checks for their artifacts. [**IPFS**](https://ipfs.tech/) is one of the content addressable system that has artifact integrity capabilities which can be complemented by all of TUF's other features.

Motivation
----------
The TUF specification provides explicit guidelines for how artifacts should be hashed and later verified to guarantee their integrity. The TUF specification leaves no room for ambiguity regarding the hashing requirements for artifacts integrity. However, Content Addressable Systems like Git, IPFS (InterPlanetary File System) and OSTree have their own mechanisms for ensuring the integrity of artifacts. When TUF is used with these systems, it is redundant for it to also ensure artifact integrity.

One solution to this problem could be to delegate the responsibility of artifact integrity verification to the content addressable systems themselves, while still using TUF to manage the metadata and provide additional security measures. By delegating the responsibility of artifact integrity verification to the content addressable system, redundancy can be avoided, reducing the overhead and complexity of the update process. This approach also enables organizations to leverage the existing mechanisms provided by content addressable systems, which are often optimized for specific use cases and can provide better performance and scalability compared to generic solutions.

Usage
-----
The repository provides an API called [``IpfsUpdater``](https://github.com/shubham4443/tuf-ipfs/blob/main/tufipfs/updater.py) which is built on top of original ``python-tuf``'s [``Updater``](https://github.com/shubham4443/python-tuf/blob/develop/tuf/ngclient/updater.py). A client with IPFS targets can initialize the ``IpfsUpdater`` to download the targets. An additional IPFS ``gateway`` property has to be specified while initializing the ``IpfsUpdater``. The ``IpfsUpdater`` uses this ``gateway`` to fetch the target over HTTP/s. The ```gateway``` can be any publicly available IPFS gateways (for e.g. ipfs.io or web3.storage) or a private gateway hosted by the client itself which is more secured (recommended).

```
updater = IpfsUpdater(
    metadata_dir='./metadatas',
    metadata_base_url='https://example.com/metadatas/',
    gateway='http://localhost:8080/', # private gateway
    target_base_url='https://example.com/targets/',
    target_dir='./targets',
)
```

An example usage can be found in [examples/client.py](https://github.com/shubham4443/tuf-ipfs/blob/main/examples/client).
