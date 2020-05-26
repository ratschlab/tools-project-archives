def create_file_with_size(path, byte_size):
    with open(path, "wb") as file:
        # sparse file that doesn't actually take up that amount of space on disk
        multiplier = int(round(byte_size))
        file.write(b"\0" * multiplier)
