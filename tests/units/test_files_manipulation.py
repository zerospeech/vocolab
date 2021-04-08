from zerospeech.utils.misc import split_zip, merge_zip


def test_zip_split_merge(large_binary_file):
    bin_file, test_location = large_binary_file

    assert bin_file.is_file(), f"Bin file [{bin_file}] needs to exist"

    res = split_zip(bin_file, chunk_max_size=50000000, hash_parts=True)
    assert res.location.is_dir(), "Parts files dir needs to exist after split!"
    assert len(list(res.location.glob('*'))) != 0, "Parts dir cannot be empty!"

    (res.location / 'fs_manifest.csv').unlink()
    res.og_filename = 'reconstructed.bin'

    res = merge_zip(res, test_location, clean=False)

    assert res.is_file(), f"file {res.name} should be in {res}"
