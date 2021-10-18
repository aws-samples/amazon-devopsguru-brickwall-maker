# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import functools
import gc
import os
import sys
import time

import psutil

SLEEP_DURATION_SECONDS = 1.0

ENV_VAR_SPEED_OF_TIME_SECONDS = "SPEED_OF_TIME_SECONDS"
ENV_VAR_BRICKWALL_HIT_DAYS = "BRICKWALL_HIT_DAYS"
ENV_VAR_BASELINE_MEMORY_UTILIZATION = "BASELINE_MEMORY_UTILIZATION"
ENV_VAR_TOTAL_MEMORY_GB = "TOTAL_MEMORY_GB"


@functools.lru_cache(maxsize=1)
def brickwall_hit_days() -> float:
    if ENV_VAR_BRICKWALL_HIT_DAYS in os.environ:
        return float(os.environ[ENV_VAR_BRICKWALL_HIT_DAYS])

    print(f"{ENV_VAR_BRICKWALL_HIT_DAYS} not set, use default of 2 days!")
    return 2


@functools.lru_cache(maxsize=1)
def speed_of_time_seconds() -> int:
    if ENV_VAR_SPEED_OF_TIME_SECONDS in os.environ:
        return int(os.environ[ENV_VAR_SPEED_OF_TIME_SECONDS])

    print(f"{ENV_VAR_SPEED_OF_TIME_SECONDS} not set, use wallclock time!")
    return 1


@functools.lru_cache(maxsize=1)
def brickwall_hit_seconds():
    return int(60 * 60 * 24 * brickwall_hit_days())


@functools.lru_cache(maxsize=1)
def wallclock_sleep_time():
    return SLEEP_DURATION_SECONDS / speed_of_time_seconds()


@functools.lru_cache(maxsize=1)
def wallclock_brickwall_hit_duration_seconds() -> int:
    return brickwall_hit_seconds() // speed_of_time_seconds()


@functools.lru_cache(maxsize=1)
def start_timestamp():
    return int(time.time())


@functools.lru_cache(maxsize=1)
def total_memory_bytes() -> int:
    if ENV_VAR_TOTAL_MEMORY_GB in os.environ:
        return int(float(os.environ[ENV_VAR_TOTAL_MEMORY_GB]) * 1024 * 1024 * 1024)
    return psutil.virtual_memory().total


def memory_tracker():
    total_bytes = 0

    def increase_memory_stat_inner(alloc_size: int):
        nonlocal total_bytes
        total_bytes += alloc_size
        return total_bytes

    return increase_memory_stat_inner


MEM_BLOCKS = []


def main():
    # Balance initial system overhead
    available = int(total_memory_bytes() * 0.95)
    alloc_size = available // brickwall_hit_seconds()
    print(
        f"Available={available} Seconds={brickwall_hit_seconds()} AllocationSize={alloc_size}"
    )
    memory_tracker_increase = memory_tracker()

    for i in range(0, brickwall_hit_seconds()):
        allocated_object = " " * alloc_size
        MEM_BLOCKS.append(allocated_object)

        curr_memory_size = memory_tracker_increase(sys.getsizeof(allocated_object))
        curr_timestamp_projection = start_timestamp() + i
        if i % 60 == 0:
            memory_utilization = curr_memory_size / total_memory_bytes() * 100
            print(curr_timestamp_projection, memory_utilization)
        time.sleep(wallclock_sleep_time())


if __name__ == "__main__":
    gc.disable()
    time.sleep(wallclock_sleep_time())
    main()
