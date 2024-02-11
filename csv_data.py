class Record:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def get_values_for_header(self, header):
        return self.data[header]


