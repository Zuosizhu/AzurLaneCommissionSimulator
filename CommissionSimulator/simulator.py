from data import *
from random import random
from config import config
from filter import filter_config


class CommissionEmulator:
    total_income = {}
    resource_tags = ['oil', 'chip', 'coin', 'cube', 'gem', 'book', 'decor_coin', 'retro', 'box', 'drill', 'plate']
    timeline = 0
    daily_done_today_count = 0
    daily_commissions_exist = []
    urgent_commissions_exist = []
    night_commissions_exist = []
    major_commissions_exist = []
    commissions_run = []
    num_set = []

    def __init__(self):
        self.daily_commissions = daily_commissions
        self.extra_commissions = extra_commissions
        self.urgent_commissions = urgent_commissions
        self.night_commissions = night_commissions
        self.major_commissions = major_commissions
        for _ in self.resource_tags:
            self.total_income[_] = 0
        # Initialize income sum

        total_rate = 0
        for _ in range(daily_commission_count):
            total_rate += daily_commissions[_]['rate']
            self.daily_commissions[_]['total_rate'] = total_rate
        total_rate = 0
        for _ in range(extra_commission_count):
            total_rate += extra_commissions[_]['rate']
            self.extra_commissions[_]['total_rate'] = total_rate
        total_rate = 0
        for _ in range(urgent_commission_count):
            total_rate += urgent_commissions[_]['rate']
            self.urgent_commissions[_]['total_rate'] = total_rate
        total_rate = 0
        for _ in range(night_commission_count):
            total_rate += night_commissions[_]['rate']
            self.night_commissions[_]['total_rate'] = total_rate
        total_rate = 0
        for _ in range(major_commission_count):
            total_rate += major_commissions[_]['rate']
            self.major_commissions[_]['total_rate'] = total_rate
        # Appearance rate summarization for random commission

        # filter_config = open(file='filter.py', mode='r', encoding='utf-8')
        # filter_line = filter_config.readline()
        # filter_list = []
        # while filter_line != '':
        #     filter_line = filter_line.replace(' ', '').rstrip('\n').lstrip('DailyEvent>')
        #     filter_list += filter_line.split('>')
        #     filter_line = filter_config.readline()
        # self.filter = filter_list
        # filter_config.close()

        self.filter = filter_config.replace('\n', '').replace(' ', '').replace('DailyEvent', '').split('>')
        self.config = config
        # Load configs

    def finish_one(self, commission_to_finish: dict):
        self.num_set.remove(commission_to_finish['num'])
        self.commissions_run.remove(commission_to_finish)
        for _k, _v in commission_to_finish.items():
            if _k in self.resource_tags:
                self.total_income[_k] += _v
        if commission_to_finish['type'] == 'Daily':
            if self.daily_done_today_count < 10:
                self.add_daily()
            else:
                self.add_extra()
        if commission_to_finish['type'] == 'Major':
            self.add_major()
        if commission_to_finish['type'] == 'Extra':
            self.add_extra()

    def add_daily(self):
        while True:
            commission_to_add = self.random_commission(commission_list=self.daily_commissions,
                                                       type_count=daily_commission_count)
            if commission_to_add['num'] in self.num_set:
                continue
            self.daily_commissions_exist.append(commission_to_add)
            self.num_set.append(commission_to_add['num'])
            self.daily_done_today_count += 1
            break

    def add_extra(self):
        while True:
            commission_to_add = self.random_commission(commission_list=self.extra_commissions,
                                                       type_count=extra_commission_count)
            if commission_to_add['num'] in self.num_set:
                continue
            self.daily_commissions_exist.append(commission_to_add)
            self.num_set.append(commission_to_add['num'])
            break

    def add_urgent(self):
        while True:
            if len(self.urgent_commissions_exist) + len(self.commissions_run) >= urgent_commission_count:
                break
            # To give up some accuracy to accelerate. A piece of shit.
            commission_to_add = \
                self.random_commission(commission_list=self.urgent_commissions, type_count=urgent_commission_count)
            if commission_to_add['num'] in self.num_set:
                continue
            commission_to_add['expire_time'] = self.timeline + commission_to_add['time_limit']
            self.urgent_commissions_exist.append(commission_to_add)
            self.num_set.append(commission_to_add['num'])
            break

    def add_major(self):
        while True:
            commission_to_add = \
                self.random_commission(commission_list=self.major_commissions, type_count=major_commission_count)
            if commission_to_add['num'] in self.num_set:
                continue
            commission_to_add['expire_time'] = self.timeline + commission_to_add['time_limit']
            self.major_commissions_exist.append(commission_to_add)
            self.num_set.append(commission_to_add['num'])
            break

    def delete_night(self):
        for _ in self.night_commissions_exist:
            self.num_set.remove(_['num'])
        self.night_commissions_exist = []

    def fill_night(self):
        for _ in range(4):
            while True:
                commission_to_add = \
                    self.random_commission(commission_list=self.night_commissions, type_count=night_commission_count)
                if commission_to_add['num'] in self.num_set:
                    continue
                self.night_commissions_exist.append(commission_to_add)
                self.num_set.append(commission_to_add['num'])
                break

    def refill_daily(self):
        count = len(self.daily_commissions_exist)
        for _ in self.daily_commissions_exist:
            self.num_set.remove(_['num'])
        self.daily_commissions_exist = []
        for _ in range(count):
            self.add_daily()

    def random_commission(self, commission_list: list, type_count: int) -> dict:
        rand = random()
        _ = int(rand // 0.025)
        if _ == 0:
            return commission_list[0]
        if _ >= type_count:
            _ = type_count - 1
        if rand > commission_list[_]['total_rate']:
            return commission_list[type_count - 1]
        # Another piece of shit to accelerate

        while not commission_list[_ - 1]['total_rate'] < rand <= commission_list[_]['total_rate']:
            if rand > commission_list[_]['total_rate']:
                _ += 1
                continue
            if rand <= commission_list[_ - 1]['total_rate']:
                _ -= 1
                if _ == 0:
                    return commission_list[0]
        return commission_list[_]

    def run_one(self):
        for filter_commission_code in self.filter:
            if 'Daily' in filter_commission_code or 'Extra' in filter_commission_code:
                for commission in self.daily_commissions_exist:
                    if filter_commission_code == commission['code']:
                        self.daily_commissions_exist.remove(commission)
                        commission_to_run = commission
                        commission_to_run['finish_time'] = self.timeline + commission['time']
                        self.commissions_run.append(commission_to_run)
                        return
            if 'Urgent' in filter_commission_code \
                    or 'Gem' in filter_commission_code or 'Ship' in filter_commission_code:
                for commission in self.urgent_commissions_exist:
                    if filter_commission_code == commission['code']:
                        self.urgent_commissions_exist.remove(commission)
                        commission_to_run = commission
                        commission_to_run['finish_time'] = self.timeline + commission['time']
                        self.commissions_run.append(commission_to_run)
                        return
            if 'Major' in filter_commission_code:
                for commission in self.major_commissions_exist:
                    if filter_commission_code == commission['code']:
                        self.major_commissions_exist.remove(commission)
                        commission_to_run = commission
                        commission_to_run['finish_time'] = self.timeline + commission['time']
                        self.commissions_run.append(commission_to_run)
                        return
            if 'Night' in filter_commission_code:
                for commission in self.night_commissions_exist:
                    if filter_commission_code == commission['code']:
                        self.night_commissions_exist.remove(commission)
                        commission_to_run = commission
                        commission_to_run['finish_time'] = self.timeline + commission['time']
                        self.commissions_run.append(commission_to_run)
                        return
            if 'shortest' == filter_commission_code.lower():
                shortest = 1000
                if len(self.daily_commissions_exist) > 0:
                    commission_to_run = self.daily_commissions_exist[0]
                else:
                    continue
                for commission in self.daily_commissions_exist:
                    if commission['time'] < shortest:
                        shortest = commission['time']
                        commission_to_run = commission
                self.daily_commissions_exist.remove(commission_to_run)
                commission_to_run['finish_time'] = self.timeline + commission_to_run['time']
                self.commissions_run.append(commission_to_run)
                return

    def run_emulate(self):
        hour = 60
        day = 24 * 60
        self.add_major()
        for _ in range(4):
            self.add_daily()
        self.timeline = 0
        while self.timeline <= self.config['time'] * day:
            if self.timeline % day == 0:
                self.daily_done_today_count = 0
                self.refill_daily()
            # If getting to the next day, refill the daily list immediately( which is what Alas does in most situations)

            if self.timeline % day == 3 * hour:
                self.delete_night()
            if self.timeline % day == 21 * hour:
                self.fill_night()

            # Cope with night commissions

            for _ in self.urgent_commissions_exist:
                if self.timeline > _['expire_time']:
                    self.urgent_commissions_exist.remove(_)
                    self.num_set.remove(_['num'])
            # Delete the expired urgent commissions in list

            for _ in self.commissions_run:
                if self.timeline > _['finish_time']:
                    self.finish_one(_)
            # Maintaining the running list
            rand = random()
            if rand < self.config['rate']:
                self.add_urgent()
            # Add urgent commissions to urgent list if success
            trial = 0
            while len(self.commissions_run) < 4 and trial <= 4:
                self.run_one()
                trial += 1

            self.timeline += 1
            # Time changed


if __name__ == '__main__':
    CE = CommissionEmulator()
    CE.run_emulate()
    for k, v in CE.total_income.items():
        print(k + ': ' + str(v))