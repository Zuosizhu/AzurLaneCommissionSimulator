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
        self.refresh_times = []
        self.last_refresh = 0
        self.running_urgent = 0
        self._priority_dirty = True
        self._cached_sorted = []

        self._in_battle = False
        self._battle_end_time = 0
        self._battle_cooldown_end = 0
        self._battle_start_event_pause = False
        self._end_time = 0
        self._pause_interval_min = 0
        self._pause_duration_min = 0

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

    def _is_event_pause_at(self, time):
        if time < self._pause_interval_min:
            return False
        adjusted = time - self._pause_interval_min
        cycle_pos = adjusted % self._pause_interval_min
        return cycle_pos < self._pause_duration_min

    def _next_pause_boundary(self, time):
        if time < self._pause_interval_min:
            return self._pause_interval_min
        adjusted = time - self._pause_interval_min
        cycle_pos = adjusted % self._pause_interval_min
        cycle_start = time - cycle_pos
        if cycle_pos < self._pause_duration_min:
            return cycle_start + self._pause_duration_min
        else:
            return cycle_start + self._pause_interval_min

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

    def _compute_oil_delta(self, from_time, to_time):
        return (to_time - from_time) * self.config['OIL_RESUME_RATE']

    def _process_scheduled_events(self):
        self.event_pause = self._is_event_pause_at(self.timeline)

        if self.timeline % WEEK == 0 and not self.event_pause:
            self.oil += self.config['OIL_GET_PER_WEEK']

        if self.timeline % DAY == 0 and not self.event_pause:
            self.oil -= self.config['OIL_OTHER_PER_DAY']

        if self.timeline % DAY == 0:
            self.daily_appear_today_count = 0
            self.daily_done_today_count = 0
            self._refill_daily()

        if self.timeline % DAY == 3 * HOUR:
            self._delete_night()

        if self.timeline % DAY == 21 * HOUR:
            self._fill_night()

    def _process_finished_commissions(self):
        finished = [c for c in self.commissions_run if self.timeline >= c.finish_time]
        for c in finished:
            self.finish_one(c)
            if not self.event_pause:
                self.oil += c.oil

    def _process_expired_urgents(self):
        expired = [c for c in self.urgent_commissions_exist if self.timeline >= c.expire_time]
        for c in expired:
            self.urgent_commissions_exist.remove(c)
            self.id_set.discard(c.id)
            self._invalidate_priority_cache()
            self._try_refresh_urgent_pool()

    def _fill_commission_slots(self):
        trial = 0
        while len(self.commissions_run) < 4 and trial <= 4:
            result = self._run_one()
            if result is False:
                break
            trial += 1

    def _can_start_battle(self):
        return self.oil >= self.total_oil_cost

    def _start_battle(self):
        self.oil -= self.total_oil_cost
        self._in_battle = True
        self._battle_start_event_pause = self.event_pause
        self._battle_end_time = self.timeline + math.ceil(self.total_battle_time)
        self.battle_run_count += 1

    def _finish_battle(self):
        self._in_battle = False
        self._generate_battle_drops()

    def _generate_battle_drops(self):
        if self._battle_start_event_pause:
            return
        if random() < self.config['MAP_DROP_RATE']:
            self._add_urgent()
        for _ in range(self.config['ELITE_COUNT']):
            if random() < self.config['ELITE_DROP_RATE']:
                self._add_urgent()
        normal = self.config['BATTLE_COUNT'] - self.config['BOSS_COUNT'] - self.config['ELITE_COUNT']
        for _ in range(normal):
            if random() < self.config['NORMAL_DROP_RATE']:
                self._add_urgent()
        for _ in range(self.config['BOSS_COUNT']):
            if random() < self.config['BOSS_DROP_RATE']:
                self._add_urgent()

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

    def _compute_next_event_time(self):
        next_time = self._end_time + 1
        today_base = (self.timeline // DAY) * DAY

        if not self._in_battle and self.commissions_run:
            earliest = min(c.finish_time for c in self.commissions_run)
            if earliest < next_time:
                next_time = earliest

        if not self._in_battle and self.urgent_commissions_exist:
            earliest = min(c.expire_time for c in self.urgent_commissions_exist)
            if earliest < next_time:
                next_time = earliest

        if self._in_battle and self._battle_end_time < next_time:
            next_time = self._battle_end_time

        if self._battle_cooldown_end > self.timeline and self._battle_cooldown_end < next_time:
            next_time = self._battle_cooldown_end

        for checkpoint in [3 * HOUR, 21 * HOUR]:
            t = today_base + checkpoint
            if t <= self.timeline:
                t += DAY
            if t < next_time:
                next_time = t

        next_day = today_base + DAY
        if next_day <= self.timeline:
            next_day += DAY
        if next_day < next_time:
            next_time = next_day

        next_week = ((self.timeline // WEEK) + 1) * WEEK
        if next_week < next_time:
            next_time = next_week

        pause_boundary = self._next_pause_boundary(self.timeline)
        if pause_boundary < next_time:
            next_time = pause_boundary

        return next_time

    def _start_simulate(self):
        self._add_major()
        for _ in range(4):
            self._add_daily()
        self.timeline = 0
        self._end_time = self.config['TIME'] * DAY
        self._pause_interval_min = self.config['EVENT_PAUSE_INTERVAL'] * DAY
        self._pause_duration_min = self.config['EVENT_PAUSE_DURATION'] * DAY
        self.total_battle_time = self.config['BATTLE_TIME'] * self.config['BATTLE_COUNT']
        normal_battles = self.config['BATTLE_COUNT'] - self.config['BOSS_COUNT']
        self.total_oil_cost = (self.config['MAP_COST_OIL'] +
                               self.config['BATTLE_COST_OIL'] * normal_battles +
                               self.config['BOSS_COST_OIL'] * self.config['BOSS_COUNT'])
        self.battle_run_count = 0
        self._battle_cooldown_end = 0
        self.event_pause = False

        while self.timeline <= self._end_time:
            self._process_scheduled_events()

            if self._in_battle and self.timeline >= self._battle_end_time:
                self._finish_battle()

            if not self._in_battle:
                self._process_expired_urgents()
                self._process_finished_commissions()
                self._fill_commission_slots()

                if not self.event_pause:
                    if self.timeline >= self._battle_cooldown_end:
                        if self._can_start_battle():
                            self._start_battle()
                            continue
                        else:
                            self._battle_cooldown_end = self.timeline + randint(120, 240)

            next_time = self._compute_next_event_time()
            if next_time <= self.timeline:
                break

            if not self.event_pause:
                self.oil += self._compute_oil_delta(self.timeline, next_time)

            self.timeline = next_time

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
