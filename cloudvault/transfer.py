import subprocess
from pathlib import Path


def copy_to_remote(source: Path, remote_file: str) -> None:
    # rclone copyto preserves the intended exact destination object path.
    subprocess.run(["rclone", "copyto", str(source), remote_file, "--retries", "3"], check=True)


def remote_sha256(remote_file: str) -> str | None:
    result = subprocess.run(["rclone", "hashsum", "SHA-256", remote_file],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    parts = result.stdout.strip().split()
    return parts[0].lower() if parts and len(parts[0]) == 64 else None


def download_to(source: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rclone", "copyto", source, str(destination)], check=True)
