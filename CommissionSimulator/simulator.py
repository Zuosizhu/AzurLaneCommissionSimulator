import math
from copy import copy
from random import random, randint

from data import *
from config import config
from filter import filter_config

from commission import Commission, dict_to_commission, compute_total_rates, random_commission, random_urgent, RESOURCE_TAGS, HOUR, DAY, WEEK
from priority import parse_filter, assign_priorities, PRIORITY_NONE
from reporter import Reporter


class CommissionSimulator:
    def __init__(self):
        self.oil = 1000
        self.total_income = {tag: 0 for tag in RESOURCE_TAGS}
        self.daily_commissions_exist = []
        self.urgent_commissions_exist = []
        self.urgent_commissions_pool = []
        self.night_commissions_exist = []
        self.major_commissions_exist = []
        self.commissions_run = []
        self.id_set = set()
        self.commissions_done = []

        self.run_shortest = False
        self.last_gem_run_out_time = 0
        self.last_gem_run_times = []
        self.timeline = 0
        self.daily_appear_today_count = 0
        self.daily_done_today_count = 0
        self.daily_done_count = 0
        self.urgent_done_count = 0
        self.extra_done_count = 0
        self.night_done_count = 0
        self.major_done_count = 0
        self.oil_consume_rate = 0
        self.event_pause = False
        self.event_pause_end = 0
        self.refresh_times = []
        self.last_refresh = 0
        self.running_urgent = 0
        self.commission_rate_per_minute = 0
        self._priority_dirty = True
        self._cached_sorted = []

        self._init_commission_data()

        self.filter = parse_filter(filter_config)
        self.config = config

        self.commissions_done = [0 for _ in range(count + 1)]

        commission_lists = {
            'Daily': self.daily_commissions,
            'Extra': self.extra_commissions,
            'Urgent': self.urgent_commissions,
            'Night': self.night_commissions,
            'Major': self.major_commissions,
        }
        self.run_shortest = assign_priorities(commission_lists, self.filter, count)
        self.priority_none = PRIORITY_NONE

        if self.run_shortest:
            self.daily_commissions = sorted(self.daily_commissions, key=lambda c: c.time)
            p = count
            for c in self.daily_commissions:
                if c.priority == PRIORITY_NONE:
                    c.priority = p
                    p -= 1
            self.daily_commissions = sorted(self.daily_commissions, key=lambda c: c.id)

        self._build_daily_and_extra()
        self.urgent_commissions_pool = [copy(c) for c in self.urgent_commissions]
        self.urgent_commissions_pool_len = urgent_commission_count
        self.urgent_id_pool_set = set(urgent_id_pool_set)

    def _init_commission_data(self):
        self.daily_commissions = [dict_to_commission(d) for d in daily_commissions]
        self.extra_commissions = [dict_to_commission(d) for d in extra_commissions]
        self.urgent_commissions = [dict_to_commission(d) for d in urgent_commissions]
        self.night_commissions = [dict_to_commission(d) for d in night_commissions]
        self.major_commissions = [dict_to_commission(d) for d in major_commissions]

        compute_total_rates(self.daily_commissions)
        compute_total_rates(self.extra_commissions)
        compute_total_rates(self.night_commissions)
        compute_total_rates(self.major_commissions)

    def _build_daily_and_extra(self):
        self.daily_and_extra_commissions = [copy(c) for c in self.extra_commissions]
        for c in self.daily_and_extra_commissions:
            c.total_rate += self.daily_commissions[-1].total_rate
        self.daily_and_extra_commissions = list(self.daily_commissions) + self.daily_and_extra_commissions

    def _invalidate_priority_cache(self):
        self._priority_dirty = True

    def finish_one(self, commission_to_finish: Commission):
        self.id_set.discard(commission_to_finish.id)
        self.commissions_done[commission_to_finish.id] += 1
        self.commissions_run.remove(commission_to_finish)
        self._invalidate_priority_cache()
        for k, v in commission_to_finish.resource_pairs():
            if k in self.total_income:
                self.total_income[k] += v
        if commission_to_finish.type == 'Urgent':
            self.running_urgent -= 1
            self._try_refresh_urgent_pool()
            self.urgent_done_count += 1
        if commission_to_finish.type in ('Daily', 'Extra'):
            if commission_to_finish.type == 'Daily':
                self.daily_done_today_count += 1
                self.daily_done_count += 1
            else:
                self.extra_done_count += 1
            if self.daily_done_today_count < 7:
                self._add_daily()
            elif self.daily_appear_today_count < 10 and self.daily_done_today_count >= 7:
                self._add_daily_or_extra()
            else:
                self._add_extra()
        if commission_to_finish.type == 'Major':
            self._add_major()
            self.major_done_count += 1
        if commission_to_finish.type == 'Night':
            self.night_done_count += 1

    def _add_daily(self):
        while True:
            commission_to_add = random_commission(self.daily_commissions)
            if commission_to_add.id in self.id_set:
                continue
            self.daily_commissions_exist.append(commission_to_add)
            self.id_set.add(commission_to_add.id)
            self.daily_appear_today_count += 1
            self._invalidate_priority_cache()
            break

    def _add_extra(self):
        while True:
            commission_to_add = random_commission(self.extra_commissions)
            if commission_to_add.id in self.id_set:
                continue
            self.daily_commissions_exist.append(commission_to_add)
            self.id_set.add(commission_to_add.id)
            self._invalidate_priority_cache()
            break

    def _add_urgent(self):
        if self.urgent_commissions_pool_len == 0:
            return False
        urgent_pool_ids = {c.id for c in self.urgent_commissions_pool}
        if urgent_pool_ids <= self.id_set:
            return False
        while True:
            commission_to_add = random_urgent(self.urgent_commissions_pool)
            if commission_to_add.id in self.id_set:
                continue
            break
        if commission_to_add.weight == 1:
            self.urgent_commissions_pool.remove(commission_to_add)
            self.urgent_id_pool_set.discard(commission_to_add.id)
        else:
            commission_to_add.weight -= 1
        self.urgent_commissions_pool_len -= 1
        commission_to_add.expire_time = self.timeline + commission_to_add.time_limit
        self.urgent_commissions_exist.append(commission_to_add)
        self.id_set.add(commission_to_add.id)
        self._invalidate_priority_cache()
        return commission_to_add

    def _add_major(self):
        while True:
            commission_to_add = random_commission(self.major_commissions)
            if commission_to_add.id in self.id_set:
                continue
            self.major_commissions_exist.append(commission_to_add)
            self.id_set.add(commission_to_add.id)
            self._invalidate_priority_cache()
            break

    def _add_daily_or_extra(self):
        while True:
            commission_to_add = random_commission(self.daily_and_extra_commissions)
            if commission_to_add.id in self.id_set:
                continue
            if commission_to_add.type == 'Daily':
                self.daily_appear_today_count += 1
            self.daily_commissions_exist.append(commission_to_add)
            self.id_set.add(commission_to_add.id)
            self._invalidate_priority_cache()
            break

    def _delete_night(self):
        for c in self.night_commissions_exist:
            self.id_set.discard(c.id)
        self.night_commissions_exist = []
        self._invalidate_priority_cache()

    def _fill_night(self):
        for _ in range(4):
            while True:
                commission_to_add = random_commission(self.night_commissions)
                if commission_to_add.id in self.id_set:
                    continue
                self.night_commissions_exist.append(commission_to_add)
                self.id_set.add(commission_to_add.id)
                self._invalidate_priority_cache()
                break

    def _refill_daily(self):
        count = len(self.daily_commissions_exist)
        for c in self.daily_commissions_exist:
            self.id_set.discard(c.id)
        self.daily_commissions_exist = []
        self._invalidate_priority_cache()
        for _ in range(count):
            self._add_daily()

    def _try_refresh_urgent_pool(self):
        if not set(gem_urgent_ids) & self.urgent_id_pool_set:
            if not self.last_gem_run_out_time:
                self.last_gem_run_out_time = self.timeline - self.last_refresh
        if (self.urgent_commissions_pool_len + len(self.urgent_commissions_exist) + self.running_urgent <= 0) \
                or (self.timeline - self.last_refresh >= DAY * 7):
            if not self.last_gem_run_out_time:
                self.last_gem_run_times.append(self.timeline - self.last_refresh)
            self.urgent_commissions_pool = [copy(c) for c in self.urgent_commissions]
            self.urgent_commissions_pool_len = urgent_commission_count
            self.urgent_id_pool_set = set(urgent_id_pool_set)
            self.refresh_times.append((self.timeline - self.last_refresh) / HOUR)
            self.last_refresh = self.timeline
            self.last_gem_run_times.append(self.last_gem_run_out_time)
            self.last_gem_run_out_time = 0

    def _handle_oil(self):
        if self.event_pause:
            return False
        if self.timeline % WEEK == 0:
            self.oil += self.config['OIL_GET_PER_WEEK']
        if self.timeline % DAY == 0:
            self.oil -= self.config['OIL_OTHER_PER_DAY']
        self.oil += self.config['OIL_RESUME_RATE']
        return True

    def _handle_battle(self):
        if self.oil < self.total_oil_cost:
            return False

        self.oil -= self.total_oil_cost
        self.timeline += math.ceil(self.total_battle_time)
        self.battle_run_count += 1

        if random() < self.config['MAP_DROP_RATE']:
            self._add_urgent()
        for _ in range(self.config['ELITE_COUNT']):
            if random() < self.config['ELITE_DROP_RATE']:
                self._add_urgent()
        normal_battles = self.config['BATTLE_COUNT'] - self.config['BOSS_COUNT'] - config['ELITE_COUNT']
        for _ in range(normal_battles):
            if random() < self.config['NORMAL_DROP_RATE']:
                self._add_urgent()
        for _ in range(self.config['BOSS_COUNT']):
            if random() < self.config['BOSS_DROP_RATE']:
                self._add_urgent()

        return True

    def _run_one(self):
        if self._priority_dirty:
            self._cached_sorted = sorted(
                self.daily_commissions_exist + self.urgent_commissions_exist +
                self.night_commissions_exist + self.major_commissions_exist,
                key=lambda c: c.priority, reverse=True
            )
            self._priority_dirty = False
        all_commissions_exist = self._cached_sorted

        if not all_commissions_exist:
            return

        if all_commissions_exist[0].priority == PRIORITY_NONE:
            if not self.run_shortest:
                return False
            shortest = 1000
            if len(self.daily_commissions_exist) > 0:
                commission_to_run = self.daily_commissions_exist[0]
            else:
                return
            for commission in self.daily_commissions_exist:
                if commission.time < shortest:
                    shortest = commission.time
                    commission_to_run = commission
            self.daily_commissions_exist.remove(commission_to_run)
            commission_to_run.finish_time = self.timeline + commission_to_run.time
            self.commissions_run.append(commission_to_run)
            self._invalidate_priority_cache()
            return

        commission_to_run = all_commissions_exist[0]
        type_dispatch = {
            'Daily': self.daily_commissions_exist,
            'Extra': self.daily_commissions_exist,
            'Urgent': self.urgent_commissions_exist,
            'Major': self.major_commissions_exist,
            'Night': self.night_commissions_exist,
        }
        target_list = type_dispatch.get(commission_to_run.type)
        if target_list is not None:
            target_list.remove(commission_to_run)
        if commission_to_run.type == 'Urgent':
            self.running_urgent += 1
        commission_to_run.finish_time = self.timeline + commission_to_run.time
        self.commissions_run.append(commission_to_run)
        self._invalidate_priority_cache()

    def _process_tick_events(self):
        if self.timeline % DAY == 0:
            self.daily_appear_today_count = 0
            self.daily_done_today_count = 0
            self._refill_daily()

        if self.timeline % (60 * DAY) == 0:
            self.event_pause = True
            self.event_pause_end = self.timeline + self.config['EVENT_PAUSE_DAYS'] // 6 * DAY

        if self.timeline >= self.event_pause_end:
            self.event_pause = False
            self.event_pause_end = 0

        if self.timeline % DAY == 3 * HOUR:
            self._delete_night()
        if self.timeline % DAY == 21 * HOUR:
            self._fill_night()

        expired = [c for c in self.urgent_commissions_exist if self.timeline > c.expire_time]
        for c in expired:
            self.urgent_commissions_exist.remove(c)
            self.id_set.discard(c.id)
            self._invalidate_priority_cache()
            self._try_refresh_urgent_pool()

        finished = [c for c in self.commissions_run if self.timeline > c.finish_time]
        for c in finished:
            self.finish_one(c)
            if not self.event_pause:
                self.oil += c.oil

        self._handle_oil()

        trial = 0
        while len(self.commissions_run) < 4 and trial <= 4:
            self._run_one()
            trial += 1

    def _compute_oil_accumulation(self, from_time, to_time):
        delta = to_time - from_time
        oil = delta * self.config['OIL_RESUME_RATE']
        first_week = ((from_time // WEEK) + 1) * WEEK
        week = first_week
        while week <= to_time:
            oil += self.config['OIL_GET_PER_WEEK']
            week += WEEK
        first_day = ((from_time // DAY) + 1) * DAY
        day = first_day
        while day <= to_time:
            oil -= self.config['OIL_OTHER_PER_DAY']
            day += DAY
        return oil

    def _next_event_time(self, max_time):
        next_time = max_time
        if self.commissions_run:
            earliest_finish = min(c.finish_time for c in self.commissions_run) + 1
            if earliest_finish < next_time:
                next_time = earliest_finish
        if self.urgent_commissions_exist:
            earliest_expire = min(c.expire_time for c in self.urgent_commissions_exist) + 1
            if earliest_expire < next_time:
                next_time = earliest_expire
        today_base = (self.timeline // DAY) * DAY
        for checkpoint in [0, 3 * HOUR, 21 * HOUR]:
            t = today_base + checkpoint
            if t > self.timeline and t < next_time:
                next_time = t
        next_day = today_base + DAY
        if next_day < next_time:
            next_time = next_day
        next_week = ((self.timeline // WEEK) + 1) * WEEK
        if next_week < next_time:
            next_time = next_week
        if self.event_pause and self.event_pause_end > self.timeline and self.event_pause_end < next_time:
            next_time = self.event_pause_end
        return next_time

    def _start_simulate(self):
        self._add_major()
        for _ in range(4):
            self._add_daily()
        self.timeline = 0
        self.oil_consume_rate = 0
        self.total_battle_time = self.config['BATTLE_TIME'] * self.config['BATTLE_COUNT']
        normal_battles = self.config['BATTLE_COUNT'] - self.config['BOSS_COUNT']
        self.total_oil_cost = self.config['MAP_COST_OIL'] + \
                               self.config['BATTLE_COST_OIL'] * normal_battles + \
                               self.config['BOSS_COST_OIL'] * self.config['BOSS_COUNT']
        self.battle_run_count = 0

        while self.timeline <= self.config['TIME'] * DAY:
            self._process_tick_events()

            if (self.oil >= self.total_oil_cost) and (not self.event_pause):
                self._handle_battle()
            else:
                if self.event_pause:
                    self.timeline += 1
                else:
                    wait_duration = randint(120, 240)
                    wait_end = self.timeline + wait_duration
                    while self.timeline < wait_end:
                        next_time = self._next_event_time(wait_end)
                        if next_time > self.timeline:
                            oil_delta = self._compute_oil_accumulation(self.timeline, next_time)
                            self.oil += oil_delta
                            self.timeline = next_time
                        self._process_tick_events()

    def run(self):
        import time
        timestamp_1 = time.time()

        reporter = Reporter(self.config, self.filter)
        reporter.validate_config()
        reporter.print_config()
        reporter.print_filter()

        self._start_simulate()

        timestamp_2 = time.time()
        reporter.print_results(self)

        print('\nTime taken: ', '%.2f' % round(timestamp_2 - timestamp_1, 2), 'Seconds')


if __name__ == '__main__':
    CS = CommissionSimulator()
    CS.run()
