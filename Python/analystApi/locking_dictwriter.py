import csv
import threading

csv_writer_lock = threading.Lock()


class LockingDictWriter:
    def __init__(self, f, fieldnames, restval="", extrasaction="raise",
                 dialect="excel", *args, **kwds):

        self.writer = csv.DictWriter(f, fieldnames, restval, extrasaction, dialect, *args, **kwds)

    def writeheader(self):
        with csv_writer_lock:
            self.writer.writeheader()

    def writerow(self, rowdict):
        with csv_writer_lock:
            return self.writer.writerow(rowdict)

    def writerows(self, rowdicts):
        with csv_writer_lock:
            return self.writer.writerows(rowdicts)
