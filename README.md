# CloudVault

**Experimental open-source backup replication for self-hosted applications.**

CloudVault v0.1.0-alpha is a proof-of-concept file inventory and rclone replication CLI. It is **not yet production-ready**, does not provide complete Discourse recovery, and must not be treated as a substitute for existing backups.

## Roadmap
- Durable file inventory and SHA-256 verification
- rclone remote transfer and restore
- Event-driven watchers, retries, versioned snapshots, encrypted storage, PostgreSQL backup coordination and recovery testing (planned)

**Safety:** Keep local attachments and existing backups. Never disable upload-inclusive Discourse backups until a complete off-server restore has been tested.

The initial implementation is being imported from the CloudVault alpha scaffold.
