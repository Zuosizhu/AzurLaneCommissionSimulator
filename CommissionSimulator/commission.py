from dataclasses import dataclass
from random import random, choice

RESOURCE_TAGS = ('oil', 'chip', 'coin', 'cube', 'gem', 'book', 'decor_coin', 'retro', 'box', 'drill', 'plate')

HOUR = 60
DAY = 24 * 60
WEEK = 7 * 24 * 60


@dataclass(eq=False)
class Commission:
    id: int
    tag: str
    name: str
    time: int
    time_limit: int
    rate: float
    type: str
    oil: float = 0.0
    chip: float = 0.0
    coin: float = 0.0
    cube: float = 0.0
    gem: float = 0.0
    book: float = 0.0
    decor_coin: float = 0.0
    retro: float = 0.0
    box: float = 0.0
    drill: float = 0.0
    plate: float = 0.0
    weight: int = 1
    total_rate: float = 0.0
    priority: int = 0
    expire_time: int = 0
    finish_time: int = 0

    def resource_pairs(self):
        for k in RESOURCE_TAGS:
            yield k, getattr(self, k)


def dict_to_commission(d: dict) -> Commission:
    return Commission(
        id=d['id'], tag=d['tag'], name=d['name'],
        time=d['time'], time_limit=d['time_limit'], rate=d['rate'],
        type=d['type'], oil=d.get('oil', 0), chip=d.get('chip', 0),
        coin=d.get('coin', 0), cube=d.get('cube', 0), gem=d.get('gem', 0),
        book=d.get('book', 0), decor_coin=d.get('decor_coin', 0),
        retro=d.get('retro', 0), box=d.get('box', 0), drill=d.get('drill', 0),
        plate=d.get('plate', 0), weight=d.get('weight', 1),
    )


def compute_total_rates(commissions: list) -> None:
    total_rate = 0.0
    for c in commissions:
        total_rate += c.rate
        c.total_rate = total_rate


def random_commission(commissions: list) -> Commission:
    rand = random()
    count = len(commissions)
    idx = int(rand * count)
    if idx == 0 and rand <= commissions[0].total_rate:
        return commissions[0]
    else:
        idx = max(1, idx)
    if idx >= count:
        idx = count - 1
    if rand > commissions[count - 1].total_rate:
        return commissions[count - 1]

    while not (commissions[idx - 1].total_rate < rand <= commissions[idx].total_rate):
        if rand > commissions[idx].total_rate:
            idx += 1
            continue
        if rand <= commissions[idx - 1].total_rate:
            idx -= 1
        if idx == 0:
            return commissions[0]
    return commissions[idx]


def random_urgent(commissions: list) -> Commission:
    return choice(commissions)