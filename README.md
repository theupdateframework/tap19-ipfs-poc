# <img src="https://i.imgur.com/eSeNsYf.png">

This repository serves the purpose of **Proof-of-Concept** implementation for [**TAP 19**](https://github.com/theupdateframework/taps/blob/master/tap19.md). The TAP explores how TUF can be adapted to content addressed ecosystems that have in-built integrity checks for their artifacts. [**IPFS**](https://ipfs.tech/) is one of the content addressable system that has artifact integrity capabilities which can be complemented by all of TUF's other features.

Motivation
----------
The TUF specification provides explicit guidelines for how artifacts should be hashed and later verified to guarantee their integrity. The TUF specification leaves no room for ambiguity regarding the hashing requirements for artifacts integrity. However, Content Addressable Systems like Git, IPFS (InterPlanetary File System) and OSTree have their own mechanisms for ensuring the integrity of artifacts. When TUF is used with these systems, it is redundant for it to also ensure artifact integrity.

One solution to this problem could be to delegate the responsibility of artifact integrity verification to the content addressable systems themselves, while still using TUF to manage the metadata and provide additional security measures. By delegating the responsibility of artifact integrity verification to the content addressable system, redundancy can be avoided, reducing the overhead and complexity of the update process. This approach also enables organizations to leverage the existing mechanisms provided by content addressable systems, which are often optimized for specific use cases and can provide better performance and scalability compared to generic solutions.
