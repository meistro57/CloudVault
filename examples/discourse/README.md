# Discourse attachment replication (experimental)

Typical host source: `/var/discourse/shared/standalone/uploads`. Mount or point to it **read-only**. Configure a dedicated rclone crypt remote and state database outside the source tree. Start with `cloudvault sync` manually, then run repeated invocations through a systemd timer once tested. Keep Discourse backups with uploads enabled until an independent full recovery drill succeeds. This alpha does not capture Discourse's PostgreSQL metadata or upload deletions.
