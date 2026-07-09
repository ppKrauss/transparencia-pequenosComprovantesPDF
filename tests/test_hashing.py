from transparencia_comprovantes.hashing import file_digest


def test_file_digest_uses_hashlib(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("abc", encoding="utf-8")

    assert file_digest(path, "sha1") == "a9993e364706816aba3e25717850c26c9cd0d89d"
