# <img src="https://i.imgur.com/eSeNsYf.png">
> **⚠️ This is still a prototype. Not recommended to use in production.**

This repository serves the purpose of **Proof-of-Concept** implementation for [**TAP 19**](https://github.com/theupdateframework/taps/blob/master/tap19.md). The TAP explores how TUF can be adapted to content addressed ecosystems that have in-built integrity checks for their artifacts. [**IPFS**](https://ipfs.tech/) is one of the content addressable system that has artifact integrity capabilities which can be complemented by all of TUF's other features.

Table of Contents
----------
- [Motivation](#motivation)
- [Usage](#usage)
- [Issue with public gateways](#issue-with-public-gateways)

Motivation
----------
The TUF specification provides explicit guidelines for how artifacts should be hashed and later verified to guarantee their integrity. The TUF specification leaves no room for ambiguity regarding the hashing requirements for artifacts integrity. However, Content Addressable Systems like Git, IPFS (InterPlanetary File System) and OSTree have their own mechanisms for ensuring the integrity of artifacts. When TUF is used with these systems, it is redundant for it to also ensure artifact integrity.

One solution to this problem could be to delegate the responsibility of artifact integrity verification to the content addressable systems themselves, while still using TUF to manage the metadata and provide additional security measures. By delegating the responsibility of artifact integrity verification to the content addressable system, redundancy can be avoided, reducing the overhead and complexity of the update process. This approach also enables organizations to leverage the existing mechanisms provided by content addressable systems, which are often optimized for specific use cases and can provide better performance and scalability compared to generic solutions.

Usage
-----
The repository provides an API called [``IpfsUpdater``](https://github.com/shubham4443/tuf-ipfs/blob/main/tufipfs/updater.py) which is built on top of original ``python-tuf``'s [``Updater``](https://github.com/shubham4443/python-tuf/blob/develop/tuf/ngclient/updater.py). A client with IPFS targets can initialize the ``IpfsUpdater`` to download the targets. An additional IPFS ``gateway`` property has to be specified while initializing the ``IpfsUpdater``. The ``IpfsUpdater`` uses this ``gateway`` to fetch the target over HTTP/s. The ```gateway``` **must be** a local gateway (see [Issue with public gateways](#issue-with-public-gateway)).

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

Issue with Public Gateways
--------
Public gateways are considered **unsafe** because their credibility cannot be validated as of now. However, this is still work in progress and we feel [Content Addressable Archives (CAR)](https://ipld.io/specs/transport/car/carv2/) could provide a solution to this issue. Until a solid fix is not available, we highly recommend to use private gateway (local IPFS node) that is trusted for integrity checks and safe from any attacks. [IPFS Desktop App](https://docs.ipfs.tech/install/ipfs-desktop/) and [Kubo](https://github.com/ipfs/kubo) offer most secure IPFS protocol implementation and widely used for running a IPFS daemon.

Additionally, the current implementation completely trusts the gateway to provide correct file for a given CID. Unfortunately, IPFS doesn't provide built-in mechanisms for guaranteeing the correctness of the data served by a specific gateway for a given CID. The data retrieved from an IPFS gateway is ultimately determined by the node that is providing the data, and there's no central authority that validates the accuracy of the content associated with a CID. This decentralized nature is both a strength and a challenge of the IPFS network. There are a few strategies you can use to enhance the likelihood of retrieving accurate content:
- **Multiple Gateways:** You can try fetching the same content from multiple different gateways and compare the results. If the content matches across different gateways, it's more likely to be accurate.
- **Content Hash Verification:** Before adding content to IPFS, you can calculate its CID locally and verify it against the CID you receive from the gateway. This way, you can ensure that the content you expect is being served.
- **Verifiable Builds:** If you're concerned about the authenticity of data, you can establish a build process where you cryptographically sign your data before adding it to IPFS. This way, you can prove that the content originated from a trusted source. 
