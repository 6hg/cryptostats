#!/usr/bin/python3
import pickle
from RepeatedTimer import RepeatedTimer
from collector import Collector, CollectorManager


class ReportCollector(Collector):
    def load(f):
        state = pickle.load(f)
        collector_root = state['current_collector_root']
        pairs = state['pairs']
        collector = ReportCollector(collector_root, pairs=pairs)

        collector.pair_volumes = {}
        with collector.file('pairs', 'r') as f:
            for line in f:
                _, exchange, pair, _, _, volume = tuple(s.strip() for s in line.split(','))
                collector.pair_volumes[(exchange, pair)] = volume

        return collector

    def generate_report(self):
        return [self.pair_report(*p) for p in self.pairs if self.is_pair_good(*p)]

    def is_pair_good(self, exchange_name, pair):
        return self.spread(exchange_name, pair) >= 0.005

    def spread(self, exchange_name, pair):
        with self.file(("spread", exchange_name, pair), "r") as f:
            spread = 0.0
            count = 0
            for l in f:
                _, ask, bid = tuple(s.strip() for s in l.split(','))
                ask = float(ask)
                bid = float(bid)
                spread += (ask-bid)/ask
                count += 1
            spread /= count
            return spread

    def pair_report(self, exchange_name, pair):
        spread = self.spread(exchange_name, pair)
        volume = self.pair_volumes[(exchange_name, pair)]
        order_count = 0
        total_time = 0
        total_volume = 0
        with self.file(('trades', exchange_name, pair), 'r') as f:
            time_start = None
            time_end = None
            for line in f:
                data = tuple(s.strip() for s in line.split(','))
                _, timestamp, _, side, price, amount, br, amount_btc = data
                amount = float(amount)
                amount_btc = float(amount_btc)
                timestamp = int(timestamp)
                if br == 'break=True':
                    if time_start is not None:
                        total_time += (time_end - time_start) / 1000
                    time_start = timestamp

                time_end = timestamp
                order_count += 1
                total_volume += amount_btc
            total_time += (time_end - time_start) / 1000
            avg_time = total_time / order_count
            avg_volume = total_volume / order_count
            return {
                'exchange': exchange_name,
                'pair': pair, 
                'volume': volume,
                'avg_time': avg_time,
                'avg_volume': avg_volume,
                'order_count': order_count,
                'spread': self.spread(exchange_name, pair)
            }


class ReportManager(CollectorManager):
    def save_state(self):
        pass

    def collect(self):
        pass

    def new_collector(self):
        time.sleep(300)
        self.load_state()


if __name__ == '__main__':
    ROOT = "/home/hukumka/src/cryptostats/data/"
    m = ReportManager(ROOT, factory=ReportCollector)
    r = m.collector.generate_report()
    print(r, m.collector)
    for i in r:
        print(i)
    