import datetime

from data import *
from random import random
from config import config
from filter import filter_config

hour = 60
day = 24 * 60

class CommissionSimulator:
    total_income = {}
    resource_tags = ['oil', 'chip', 'coin', 'cube', 'gem', 'book', 'decor_coin', 'retro', 'box', 'drill', 'plate']
    timeline = 0
    daily_appear_today_count = 0
    daily_done_today_count = 0
    daily_commissions_exist = []
    urgent_commissions_exist = []
    urgent_commissions_pool = []
    night_commissions_exist = []
    major_commissions_exist = []
    commissions_run = []
    id_set = []
    commissions_done = []
    daily_done_count = 0

    def __init__(self):
        self.last_refresh = 0
        self.running_urgent = 0
        self.daily_commissions = daily_commissions[:]
        self.extra_commissions = extra_commissions[:]
        self.urgent_commissions = urgent_commissions[:]
        self.night_commissions = night_commissions[:]
        self.major_commissions = major_commissions[:]
        self.urgent_commissions_pool = urgent_commissions[:]
        self.urgent_commissions_pool_len = urgent_commission_count
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

        from copy import deepcopy
        self.daily_and_extra_commissions = deepcopy(self.extra_commissions)
        for _ in range(len(self.daily_and_extra_commissions)):
            self.daily_and_extra_commissions[_]['total_rate'] += daily_commissions[-1]['total_rate']
        self.daily_and_extra_commissions = self.daily_commissions[:] + self.daily_and_extra_commissions[:]
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

        self.commissions_done = [0 for _ in range(count + 1)]
        priority = count + 1

        for _ in self.daily_commissions:
            _['priority'] = -priority
        for _ in self.extra_commissions:
            _['priority'] = -priority
        for _ in self.urgent_commissions:
            _['priority'] = -priority
        for _ in self.night_commissions:
            _['priority'] = -priority
        for _ in self.major_commissions:
            _['priority'] = -priority
        self.priority_none = -priority

        for commission in self.filter:
            priority -= 1
            if 'Daily' in commission:
                for _ in range(len(self.daily_commissions)):
                    if commission == self.daily_commissions[_]['tag']:
                        self.daily_commissions[_]['priority'] = priority
                continue
            if 'Night' in commission:
                for _ in range(len(self.night_commissions)):
                    if commission == self.night_commissions[_]['tag']:
                        self.night_commissions[_]['priority'] = priority
                continue
            if 'Major' in commission:
                for _ in range(len(self.major_commissions)):
                    if commission == self.major_commissions[_]['tag']:
                        self.major_commissions[_]['priority'] = priority
                continue
            if 'Extra' in commission:
                for _ in range(len(self.extra_commissions)):
                    if commission == self.extra_commissions[_]['tag']:
                        self.extra_commissions[_]['priority'] = priority
                continue
            if 'Urgent' in commission or 'Gem' in commission or 'Ship' in commission:
                for _ in range(len(self.urgent_commissions)):
                    if commission == self.urgent_commissions[_]['tag']:
                        self.urgent_commissions[_]['priority'] = priority
                continue
            if 'shortest' == commission.lower():
                self.daily_commissions = sorted(daily_commissions, key=lambda _: _['time'])
                for _ in range(len(self.daily_commissions)):
                    if daily_commissions[_]['priority'] == self.priority_none:
                        self.daily_commissions[_]['priority'] = priority
                        priority -= 1
                self.daily_commissions = sorted(daily_commissions, key=lambda _: _['id'])
                priority += 1

    def finish_one(self, commission_to_finish: dict):
        self.id_set.remove(commission_to_finish['id'])
        self.commissions_done[commission_to_finish['id']] += 1
        self.commissions_run.remove(commission_to_finish)
        for _k, _v in commission_to_finish.items():
            if _k in self.resource_tags:
                self.total_income[_k] += _v
        if commission_to_finish['type'] == 'Urgent':
            self.running_urgent -=1
            self.try_refresh_urgent_pool()
        if commission_to_finish['type'] == 'Daily' or commission_to_finish['type'] == 'Extra':
            if commission_to_finish['type'] == 'Daily':
                self.daily_done_today_count += 1
                # self.daily_done_count += 1
            # if self.daily_appear_today_count < 10 and self.daily_done_today_count < 7:
            if self.daily_done_today_count < 7:
                self.add_daily()
            elif self.daily_appear_today_count < 10 and self.daily_done_today_count >= 7:
                self.add_daily_or_extra()
            else:
                self.add_extra()
        if commission_to_finish['type'] == 'Major':
            self.add_major()

    def add_daily(self):
        while True:
            commission_to_add = self.random_commission(commission_list=self.daily_commissions,
                                                       type_count=daily_commission_count)
            if commission_to_add['id'] in self.id_set:
                continue
            self.daily_commissions_exist.append(commission_to_add)
            self.id_set.append(commission_to_add['id'])
            self.daily_appear_today_count += 1
            break

    def add_extra(self):
        while True:
            commission_to_add = self.random_commission(commission_list=self.extra_commissions,
                                                       type_count=extra_commission_count)
            if commission_to_add['id'] in self.id_set:
                continue
            self.daily_commissions_exist.append(commission_to_add)
            self.id_set.append(commission_to_add['id'])
            break

    def add_urgent(self):
        while True:
            # if len(self.urgent_commissions_exist) + len(self.commissions_run) >= urgent_commission_count:
            #     break
            # To give up some accuracy to accelerate. A piece of shit. Expired
            if self.urgent_commissions_pool_len == 0:
                break
            urgent_pool_ids = [d.get('id', 0) for d in self.urgent_commissions_pool]
            _break = True
            for id in urgent_pool_ids:
                if id not in self.id_set:
                    _break = False
            if _break:
                break
            commission_to_add = \
                self.random_commission(commission_list=self.urgent_commissions_pool, type_count=self.urgent_commissions_pool_len)
            if commission_to_add['id'] in self.id_set:
                continue
            for _ in range(self.urgent_commissions_pool_len):
                if self.urgent_commissions_pool[_] == commission_to_add:
                    del self.urgent_commissions_pool[_]
                    self.urgent_commissions_pool_len -= 1
                    break
            total_rate = 0
            for _ in range(self.urgent_commissions_pool_len):
                total_rate += self.urgent_commissions_pool[_]['rate']
                self.urgent_commissions_pool[_]['total_rate'] = total_rate
            ratio = 1/total_rate if total_rate != 0 else 1
            for _ in range(self.urgent_commissions_pool_len):
                self.urgent_commissions_pool[_]['total_rate'] = self.urgent_commissions_pool[_]['total_rate']*ratio
            # Maintaining urgent pool
            commission_to_add['expire_time'] = self.timeline + commission_to_add['time_limit']
            self.urgent_commissions_exist.append(commission_to_add)
            self.id_set.append(commission_to_add['id'])
            break

    def add_major(self):
        while True:
            commission_to_add = \
                self.random_commission(commission_list=self.major_commissions, type_count=major_commission_count)
            if commission_to_add['id'] in self.id_set:
                continue
            self.major_commissions_exist.append(commission_to_add)
            self.id_set.append(commission_to_add['id'])
            break

    def add_daily_or_extra(self):
        while True:
            commission_to_add = \
                self.random_commission(commission_list=self.daily_and_extra_commissions,
                                       type_count=daily_commission_count+extra_commission_count)
            if commission_to_add['id'] in self.id_set:
                continue
            if commission_to_add['type'] =='Daily':
                self.daily_appear_today_count += 1
            self.daily_commissions_exist.append(commission_to_add)
            self.id_set.append(commission_to_add['id'])
            break

    def delete_night(self):
        for _ in self.night_commissions_exist:
            self.id_set.remove(_['id'])
        self.night_commissions_exist = []

    def fill_night(self):
        for _ in range(4):
            while True:
                commission_to_add = \
                    self.random_commission(commission_list=self.night_commissions, type_count=night_commission_count)
                if commission_to_add['id'] in self.id_set:
                    continue
                self.night_commissions_exist.append(commission_to_add)
                self.id_set.append(commission_to_add['id'])
                break

    def refill_daily(self):
        count = len(self.daily_commissions_exist)
        for _ in self.daily_commissions_exist:
            self.id_set.remove(_['id'])
        self.daily_commissions_exist = []
        for _ in range(count):
            self.add_daily()

    def random_commission(self, commission_list: list, type_count: int) -> dict:
        rand = random()
        _ = int(rand * type_count)
        if _ == 0 and rand <= commission_list[0]['total_rate']:
            return commission_list[0]
        else:
            _ = max(1, _)
        if _ >= type_count:
            _ = type_count - 1
        if rand > commission_list[type_count - 1]['total_rate']:
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


    def try_refresh_urgent_pool(self):
        if (self.urgent_commissions_pool_len + len(self.urgent_commissions_exist) + self.running_urgent <= 0)\
                or (self.timeline - self.last_refresh >= day*7):
            self.urgent_commissions_pool = urgent_commissions[:]
            self.urgent_commissions_pool_len = urgent_commission_count
            self.last_refresh = self.timeline

    def run_one(self):
        # for filter_commission_tag in self.filter:
        #     if 'Daily' in filter_commission_tag or 'Extra' in filter_commission_tag:
        #         for commission in self.daily_commissions_exist:
        #             if filter_commission_tag == commission['tag']:
        #                 self.daily_commissions_exist.remove(commission)
        #                 commission_to_run = commission
        #                 commission_to_run['finish_time'] = self.timeline + commission['time']
        #                 self.commissions_run.append(commission_to_run)
        #                 return
        #     if 'Urgent' in filter_commission_tag \
        #             or 'Gem' in filter_commission_tag or 'Ship' in filter_commission_tag:
        #         for commission in self.urgent_commissions_exist:
        #             if filter_commission_tag == commission['tag']:
        #                 self.urgent_commissions_exist.remove(commission)
        #                 commission_to_run = commission
        #                 commission_to_run['finish_time'] = self.timeline + commission['time']
        #                 self.commissions_run.append(commission_to_run)
        #                 return
        #     if 'Major' in filter_commission_tag:
        #         for commission in self.major_commissions_exist:
        #             if filter_commission_tag == commission['tag']:
        #                 self.major_commissions_exist.remove(commission)
        #                 commission_to_run = commission
        #                 commission_to_run['finish_time'] = self.timeline + commission['time']
        #                 self.commissions_run.append(commission_to_run)
        #                 return
        #     if 'Night' in filter_commission_tag:
        #         for commission in self.night_commissions_exist:
        #             if filter_commission_tag == commission['tag']:
        #                 self.night_commissions_exist.remove(commission)
        #                 commission_to_run = commission
        #                 commission_to_run['finish_time'] = self.timeline + commission['time']
        #                 self.commissions_run.append(commission_to_run)
        #                 return

        all_commissions_exist = self.daily_commissions_exist + self.urgent_commissions_exist + \
                                self.night_commissions_exist + self.major_commissions_exist
        all_commissions_exist = sorted(all_commissions_exist, key=lambda _: _['priority'], reverse=True)

        if all_commissions_exist[0]['priority'] == self.priority_none:
            shortest = 1000
            if len(self.daily_commissions_exist) > 0:
                commission_to_run = self.daily_commissions_exist[0]
            else:
                return
            for commission in self.daily_commissions_exist:
                if commission['time'] < shortest:
                    shortest = commission['time']
                    commission_to_run = commission
            self.daily_commissions_exist.remove(commission_to_run)
            commission_to_run['finish_time'] = self.timeline + commission_to_run['time']
            self.commissions_run.append(commission_to_run)
            return

        commission_to_run = all_commissions_exist[0]
        if commission_to_run['type'] == 'Daily' or commission_to_run['type'] == 'Extra':
            self.daily_commissions_exist.remove(commission_to_run)
            commission_to_run['finish_time'] = self.timeline + commission_to_run['time']
            self.commissions_run.append(commission_to_run)
            return
        if commission_to_run['type'] == 'Urgent':
            self.running_urgent+=1
            self.urgent_commissions_exist.remove(commission_to_run)
            commission_to_run['finish_time'] = self.timeline + commission_to_run['time']
            self.commissions_run.append(commission_to_run)
            return
        if commission_to_run['type'] == 'Major':
            self.major_commissions_exist.remove(commission_to_run)
            commission_to_run['finish_time'] = self.timeline + commission_to_run['time']
            self.commissions_run.append(commission_to_run)
            return
        if commission_to_run['type'] == 'Night':
            self.night_commissions_exist.remove(commission_to_run)
            commission_to_run['finish_time'] = self.timeline + commission_to_run['time']
            self.commissions_run.append(commission_to_run)
            return

    def run_emulate(self):
        self.add_major()
        for _ in range(4):
            self.add_daily()
        self.timeline = 0
        while self.timeline <= self.config['time'] * day:
            if self.timeline % day == 0:
                self.daily_appear_today_count = 0
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
                    self.id_set.remove(_['id'])
                    self.try_refresh_urgent_pool()
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
    import time
    timestamp_1 = time.time()
    CS = CommissionSimulator()
    if CS.config['time'] <= 0 or not 0 <= CS.config['rate'] <= 1:
        exit('Illegal config.')
    CS.run_emulate()
    timestamp_2 = time.time()
    print(f'Time: {CS.config["time"]} Days | Drop rate: {CS.config["rate"]}')
    max_len_total = len('%.4f' % round(CS.total_income['oil'], 4))
    commissions = daily_commissions + extra_commissions + major_commissions + urgent_commissions + night_commissions

    if CS.config['print_filter']:
        print('\nFilter:')
        if '' in CS.filter:
            CS.filter.remove('')
        item_in_one_line = 1
        print('DailyEvent >')
        for _ in range(len(CS.filter)):
            if _ == len(CS.filter)-1:
                if item_in_one_line == 1:
                    print(CS.filter[_])
                else:
                    print('\n' + CS.filter[_])
                break
            if item_in_one_line < 5:
                print(CS.filter[_] + ' > ', end='')
                item_in_one_line += 1
            else:
                print(CS.filter[_] + ' >')
                item_in_one_line = 1
    if CS.config['print_commission_done']:
        print('\nCommissions done:')
        # print('Daily commissions done count:', CE.daily_done_count)
        for _ in range(count):
            if CS.commissions_done[_ + 1] == 0:
                continue
            print('  ' + commissions[_]['name'] + ': ', CS.commissions_done[_ + 1])

    print('\nIncome:')
    for k, v in CS.total_income.items():
        k = k.capitalize()
        t = '%.4f' % round(v, 4)
        v = '%.4f' % round(v / CS.config['time'], 4)
        print('  ' + k + (10 - len(k)) * ' ' + ': ' + ((10 - len(v)) * ' ') + v + '/Day' + '     Total:' +
              (max_len_total + 1 - len(t)) * ' ' + t)
    print('\nTime taken: ', '%.2f' % round(timestamp_2 - timestamp_1, 2), 'Seconds')
