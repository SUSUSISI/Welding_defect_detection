from datetime import datetime
import random as rd
import numpy as np
import FaDAm as fd


def generate(base_current, base_voltage, base_wire_feed,
             init_current, init_voltage, init_wire_feed, duration):
    current_duration = 0

    new_data = fd.GTAW.GTAW_data()
    new_data.label = 'porosity'

    init_ramp_duration = rd.random() / 2
    current_duration += init_ramp_duration

    for t in np.arange(0, init_ramp_duration, 0.1):
        init_current = rd.uniform(init_current, base_current)
        init_voltage = rd.uniform(init_voltage, base_voltage)
        init_wire_feed = rd.uniform(init_wire_feed, base_wire_feed)

        new_data.append_data([init_current, init_voltage, init_wire_feed])

    init_duration = rd.randrange(1, 2)
    current_duration += init_duration

    for t in np.arange(0, init_duration, 0.1):
        init_current = base_current + base_current * rd.uniform(0.03, 0.07)
        init_voltage = base_voltage + base_voltage * rd.uniform(0.03, 0.07)
        init_wire_feed = base_wire_feed + base_voltage * rd.uniform(0, 0.05)

        new_data.append_data([init_current, init_voltage, init_wire_feed])

    process_duration = duration - current_duration
    undercut_init = rd.uniform(0.0, process_duration)
    undercut_duration = rd.randrange(1, 5)

    process_range = np.arange(0, process_duration, 0.02)

    skewed_current = base_current - base_current * rd.uniform(0.1, 0.15)
    skewed_voltage = base_voltage - base_voltage * rd.uniform(0.1, 0.15)
    skewed_wire_feed = base_wire_feed - base_voltage * rd.uniform(0.1, 0.15)

    for t in np.arange(0, process_duration, 0.1):
        if t > undercut_init and t < undercut_init + undercut_duration:
            noised_data = fd.GTAW.generate_noised_data([skewed_current, skewed_voltage, skewed_wire_feed],
                                                       noise_ratio=0.03)
        else:
            noised_data = fd.GTAW.generate_noised_data([base_current, base_voltage, base_wire_feed], noise_ratio=0.03)

        new_data.append_data(noised_data)

    current_duration += process_duration

    final_ramp_duration = rd.random() / 2

    last_data = new_data.data[-1]
    final_current = last_data[0]
    final_voltage = last_data[1]
    final_wire_feed = last_data[2]

    for t in np.arange(0, final_ramp_duration, 0.1):
        final_current = rd.uniform(7.4, final_current)
        final_voltage = rd.uniform(0, final_current)
        final_wire_feed = rd.uniform(0, final_wire_feed)

        new_data.append_data([final_current, final_voltage, final_wire_feed])

    return new_data
