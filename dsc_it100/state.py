

class GeneralStatus(object):
    battery_trouble = False
    ac_trouble = False
    bell_trouble = False


class PartitionStatus(object):
    ready = False
    alarm = False
    trouble = False
    armed_away = False
    armed_stay = False
    exit_delay = False
    entry_delay = False


class Partition(object):
    index = None
    status = None

    def __init__(self, index):
        self.index = index
        self.status = PartitionStatus()


class ZoneStatus(object):
    open = False
    fault = False
    alarm = False
    tamper = False


class Zone(object):
    index = None
    status = None

    def __init__(self, index):
        self.index = index
        self.status = ZoneStatus()


class AlarmState(object):
    """
    State of the alarm system.
    """

    def __init__(self):
        self.status = GeneralStatus()
        self.partitions = {}
        self.zones = {}

    def _update(self, item, update):
        for key, value in update.items():
            if isinstance(value, dict):
                self._update(getattr(item, key), value)
            else:
                setattr(item, key, value)

    def update_general(self, update):
        self._update(self.status, update)
        return self.status

    def update_zone(self, zone, update):
        zone = self.get_zone(zone)
        self._update(zone, update)
        return zone

    def update_partition(self, partition, update):
        partition = self.get_partition(partition)
        self._update(partition, update)
        return partition

    def get_zone(self, index):
        if index not in self.zones:
            self.zones[index] = Zone(index)

        return self.zones[index]

    def get_partition(self, index):
        if index not in self.partitions:
            self.partitions[index] = Partition(index)

        return self.partitions[index]
