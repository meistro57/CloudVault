"""CloudVault experimental CLI. No source-file deletion."""
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path, PurePosixPath
from .manifest import sha256_file
from .queue import connect
from .transfer import copy_to_remote, download_to, remote_sha256


def safe_relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def remote_name(remote: str, relative: str) -> str:
    return remote.rstrip("/") + "/" + relative


def scan(root: Path, conn: sqlite3.Connection, remote: str, stable_seconds: int) -> int:
    count = 0
    now = time.time()
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        before = path.stat()
        if now - before.st_mtime < stable_seconds:
            continue
        relative = safe_relative(root, path)
        row = conn.execute("SELECT size,mtime_ns,sha256,status FROM files WHERE path=?", (relative,)).fetchone()
        if row and row[0] == before.st_size and row[1] == before.st_mtime_ns and row[3] == "verified":
            continue
        digest = sha256_file(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            continue
        conn.execute("""INSERT INTO files(path,size,mtime_ns,sha256,remote_path,status,attempts,last_error)
            VALUES(?,?,?,?,?,'pending',0,NULL)
            ON CONFLICT(path) DO UPDATE SET size=excluded.size,mtime_ns=excluded.mtime_ns,
            sha256=excluded.sha256,remote_path=excluded.remote_path,status='pending',attempts=0,last_error=NULL,
            updated_at=CURRENT_TIMESTAMP""", (relative, after.st_size, after.st_mtime_ns, digest, remote_name(remote,relative)))
        count += 1
    conn.commit()
    return count


def process(root: Path, conn: sqlite3.Connection, limit: int) -> tuple[int,int]:
    success = failure = 0
    rows = conn.execute("SELECT path,size,mtime_ns,sha256,remote_path FROM files WHERE status IN ('pending','failed') ORDER BY updated_at LIMIT ?", (limit,)).fetchall()
    for relative, size, mtime_ns, digest, remote in rows:
        source = root / relative
        try:
            if not source.is_file() or source.is_symlink():
                raise RuntimeError("Source missing or symlink")
            st = source.stat()
            if st.st_size != size or st.st_mtime_ns != mtime_ns or sha256_file(source) != digest:
                raise RuntimeError("Source changed since inventory; rescan required")
            copy_to_remote(source, remote)
            # Some remotes (including Drive) cannot provide SHA-256 directly.
            # Independently download and hash to verify bytes, without local temp storage.
            remote_digest = remote_sha256(remote)
            if remote_digest is None:
                import hashlib
                import subprocess
                hasher = hashlib.sha256()
                with subprocess.Popen(["rclone", "cat", remote], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                    for chunk in iter(lambda: proc.stdout.read(1024 * 1024), b""):
                        hasher.update(chunk)
                    stderr = proc.stderr.read()
                    if proc.wait() != 0:
                        raise RuntimeError("Remote readback failed: " + stderr.decode(errors="replace")[-500:])
                remote_digest = hasher.hexdigest()
            if remote_digest != digest:
                raise RuntimeError("Remote checksum mismatch")
            conn.execute("UPDATE files SET status='verified',attempts=attempts+1,last_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE path=?",(relative,))
            success += 1
        except Exception as exc:
            conn.execute("UPDATE files SET status='failed',attempts=attempts+1,last_error=?,updated_at=CURRENT_TIMESTAMP WHERE path=?",(str(exc)[:1000],relative))
            failure += 1
        conn.commit()
    return success,failure


def restore(conn: sqlite3.Connection, destination: Path) -> int:
    rows = conn.execute("SELECT path,sha256,remote_path FROM files WHERE status='verified'").fetchall()
    for relative, digest, remote in rows:
        # Protect against traversal if the manifest database was tampered with.
        parts = PurePosixPath(relative).parts
        if not parts or any(x in ('.','..') for x in parts) or relative.startswith('/'):
            raise RuntimeError("Unsafe restore path")
        output = destination.joinpath(*parts)
        if output.exists():
            raise RuntimeError(f"Refusing to overwrite {output}")
        download_to(remote, output)
        if sha256_file(output) != digest:
            raise RuntimeError(f"Restore checksum mismatch: {relative}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="CloudVault alpha: file replication, not yet a complete backup system")
    parser.add_argument("command", choices=["scan","sync","status","restore"])
    parser.add_argument("--source", type=Path, default=Path(os.environ.get("CLOUDVAULT_SOURCE", "/source")))
    parser.add_argument("--database", type=Path, default=Path(os.environ.get("CLOUDVAULT_DB", "/state/cloudvault.sqlite3")))
    parser.add_argument("--remote", default=os.environ.get("CLOUDVAULT_REMOTE", ""))
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--stable-seconds", type=int, default=60)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.command in ("scan","sync") and (not args.remote or ':' not in args.remote):
        parser.error("--remote must be an existing rclone remote path, e.g. vault:backups/uploads")
    if args.command in ("scan","sync") and not args.source.is_dir():
        parser.error("--source must be an existing directory")
    conn = connect(args.database)
    if args.command in ("scan","sync"):
        discovered = scan(args.source,conn,args.remote,args.stable_seconds)
        print(f"Inventoried {discovered} new/changed files")
        if args.command == "sync":
            ok,failed = process(args.source,conn,args.limit)
            print(f"Verified: {ok}; failed: {failed}")
            if failed: sys.exit(1)
    elif args.command == "status":
        print(json.dumps(dict(conn.execute("SELECT status,COUNT(*) FROM files GROUP BY status").fetchall()),indent=2))
    else:
        if args.destination is None:
            parser.error("restore requires --destination")
        print(f"Restored and verified {restore(conn,args.destination)} files")

if __name__ == "__main__":
    main()
