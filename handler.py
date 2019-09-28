from tabulate import tabulate
from settings import TABLE_HEADERS


class Handler:

    def __init__(self, data):
        self.data = data
        self.handled_data = []

    def run(self):
        for key, val in self.data.items():
            self.handled_data.append([
                key,
                len(val['prices']),
                sum(val['prices']),
                sum(val['prices']) / len(val['prices']),
                max(val['prices']),
                min(val['prices']),
                val['views']
            ])

    def display(self):
        print(tabulate(
            self.handled_data,
            headers=TABLE_HEADERS,
            tablefmt='orgtbl'
        ))
