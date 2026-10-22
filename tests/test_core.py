import tempfile
import unittest
from pathlib import Path
from cloudvault.manifest import sha256_file
from cloudvault.queue import connect
from cloudvault.cli import scan, remote_name

class CloudVaultTests(unittest.TestCase):
    def test_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"file.txt"
            p.write_bytes(b"hello")
            self.assertEqual(sha256_file(p), "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"source"
            root.mkdir()
            (root/"hello.txt").write_text("hello")
            conn=connect(Path(tmp)/"state"/"db.sqlite3")
            self.assertEqual(scan(root,conn,"crypt:files",0),1)
            self.assertEqual(scan(root,conn,"crypt:files",0),1) # pending remains retryable
            self.assertEqual(conn.execute("SELECT status FROM files").fetchone()[0],"pending")
            self.assertEqual(remote_name("crypt:files","hello.txt"),"crypt:files/hello.txt")

if __name__ == "__main__": unittest.main()
