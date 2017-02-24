#!/usr/bin/env python3

import asyncio

import dsc_it100


def handle_zone_update(driver, zone):
    print("Zone {} has changed state: open={} fault={} alarm={} tamper={}".format(
        zone.index,
        zone.status.open,
        zone.status.fault,
        zone.status.alarm,
        zone.status.tamper,
    ))


def handle_partition_update(driver, partition):
    print("Partition {} has changed state: ready={} alarm={} trouble={}".format(
        partition.index,
        partition.status.ready,
        partition.status.alarm,
        partition.status.trouble,
    ))


def handle_general_update(driver, general):
    print("General state has updated: battery_trouble={} ac_trouble={} bell_trouble={}".format(
        general.battery_trouble,
        general.ac_trouble,
        general.bell_trouble,
    ))

loop = asyncio.get_event_loop()
driver = dsc_it100.Driver('/dev/ttyUSB0', loop)
driver.set_alarm_code('1234')
driver.handler_zone_update = handle_zone_update
driver.handler_partition_update = handle_partition_update
driver.handler_general_update = handle_general_update
driver.connect()
loop.run_forever()
loop.close()
