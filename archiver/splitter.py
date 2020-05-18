import os
from . import helpers

SORT_ORDER_DESCENDING = True


class Splitter:
    archives = []
    package_size = 0

    def __init__(self, max_size):
        self.max_size = max_size

    def split_directory(self, source_path):
        self.__split(source_path, True)
        return self.archives

    def __split(self, source_path, top=False):
        appended = False
        current_package = []
        sorted_listing = helpers.get_sorted_listing(source_path, SORT_ORDER_DESCENDING)

        for element in sorted_listing:
            element_path = source_path.joinpath(element)
            element_size = helpers.get_size_of_path(element_path)

            if self.package_size + element_size < self.max_size:
                current_package.append(element_path)
                self.package_size += element_size
            elif element_size < self.max_size:
                appended = True
                self.package_size = element_size
                self.archives.append(current_package)

                current_package = [element_path]
            elif element_path.is_dir():
                current_package = self.__split(element_path)
            else:
                raise ValueError("Some files are larger than the maximum package size")

        return_val = current_package

        if not appended:
            self.archives.append(current_package)
            current_package = []

        return return_val
