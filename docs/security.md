# Security notes

Never publish OAuth tokens, rclone.conf, encryption keys, private uploads, or manifests containing private paths. Prefer a dedicated restricted Google account/remote and an rclone crypt overlay. Protect the SQLite database; it contains paths and content hashes. Store encryption keys and a manifest backup separately from the remote. Remote verification is a content readback, not a guarantee of remote immutability. Test restores regularly. Never remove live Discourse attachments based solely on CloudVault status.
