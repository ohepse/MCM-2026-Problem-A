import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# ==========================================
# 0. Global Style Settings (Large & Bold)
# ==========================================
plt.rcParams.update({
    'font.size': 16,
    'font.weight': 'bold',
    'axes.labelweight': 'bold',
    'axes.titleweight': 'bold',
    'figure.titleweight': 'bold',
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 14
})

# ==========================================
# 1. Simulation Setup
# ==========================================

# Battery Simulation Model
def get_ocv_corrected(soc):
    return 3.2 + 0.9 * soc + 0.3 * (soc**2)

class BatterySim:
    def __init__(self, capacity_mah=4575):
        self.Q_coulomb = capacity_mah * 3.6
        self.R0 = 0.05
        self.Rp = 0.03
        self.Cp = 2000
        self.tau = self.Rp * self.Cp
        self.cutoff_voltage = 3.0
        self.soc = 1.0
        self.up = 0.0
        
    def step(self, power_w, dt=1.0):
        ocv = get_ocv_corrected(self.soc)
        a = self.R0
        b = -(ocv - self.up)
        c = power_w
        delta = b**2 - 4*a*c
        if delta < 0: return None, None, None
        I_load = (-b - np.sqrt(delta)) / (2*a)
        v_term = ocv - self.up - I_load * self.R0
        if v_term < self.cutoff_voltage or self.soc <= 0:
            return v_term, I_load, 0.0
        self.soc -= (I_load * dt) / self.Q_coulomb
        self.up = self.up * np.exp(-dt/self.tau) + I_load * self.Rp * (1 - np.exp(-dt/self.tau))
        return v_term, I_load, self.soc

# Schedule
P_HIGH, P_MED, P_LOW = 3.87, 2.21, 1.00
schedule = [
    (0.5, P_MED, "Medium"), (2.5, P_LOW, "Low"), (1.0, P_MED, "Medium"),
    (1.0, P_HIGH, "High"), (3.0, P_LOW, "Low"), (1.5, P_MED, "Medium"),
    (2.0, P_HIGH, "High"), (2.0, P_MED, "Medium"), (1.5, P_LOW, "Low")
]

sim = BatterySim()
start_time = datetime(2024, 1, 1, 9, 0, 0)
time_points, soc_points, voltage_points = [], [], []
current_time = start_time
dt = 1.0; is_dead = False; dead_time = None

for duration_h, power, label in schedule:
    if is_dead: break
    steps = int(duration_h * 3600)
    for _ in range(steps):
        v, i, s = sim.step(power, dt)
        if v is None or s <= 0:
            is_dead = True; dead_time = current_time; break
        if current_time.second == 0:
            time_points.append(current_time)
            soc_points.append(s * 100)
            voltage_points.append(v)
        current_time += timedelta(seconds=dt)

# ==========================================
# 2. Plotting: Modified (No Power Curve, Distinct Background)
# ==========================================

fig, ax1 = plt.subplots(figsize=(16, 10))

# 1. SoC (Left Axis)
p1, = ax1.plot(time_points, soc_points, "grey", linewidth=3, label="SoC (%)")
ax1.set_xlabel("Time of Day")
ax1.set_ylabel("SoC (%)")
ax1.set_ylim(0, 105)
ax1.tick_params(axis='y', colors=p1.get_color())
ax1.yaxis.label.set_color(p1.get_color())

# 2. Voltage (Right Axis)
ax2 = ax1.twinx()
p2, = ax2.plot(time_points, voltage_points, "k-", linewidth=2.5, label="Voltage (V)")
ax2.set_ylabel("Voltage (V)")
ax2.set_ylim(2.5, 4.5)
ax2.tick_params(axis='y', colors=p2.get_color())
ax2.yaxis.label.set_color(p2.get_color())

# 3. Background Phases (More distinct: alpha=0.5)
# Using slightly more saturated colors to make them pop more
phase_colors = {
    P_HIGH: '#D98880', # Stronger Red
    P_MED: '#7FB3D5',  # Stronger Orange
    P_LOW: '#8FBC8F'   # Stronger Blue/Purple
}
curr = start_time
for duration_h, power, label in schedule:
    end = curr + timedelta(hours=duration_h)
    if is_dead and end > dead_time: end = dead_time
    
    # Increased alpha to 0.4 for visibility
    ax1.axvspan(curr, end, color=phase_colors[power], alpha=0.4)
    
    #Label
    mid = curr + (end - curr)/2
    if duration_h >= 1.0 and (not is_dead or mid < dead_time):
        ax1.text(mid, 50, label, ha='center', va='center', fontsize=16, rotation=0, color='black', fontweight='bold')
    
    curr = end
    if is_dead and curr >= dead_time: break

# Dead Time Marker
if is_dead:
    ax1.axvline(dead_time, color='red', linestyle='--', linewidth=3)
    ax1.text(dead_time, 16, f' DRAINED\n {dead_time.strftime("%H:%M")}', color='red', fontweight='bold', fontsize=18, ha='left')

# Legend
lines = [p1, p2]
ax1.legend(lines, [l.get_label() for l in lines], loc='upper right')

# Formatting
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

plt.tight_layout()
plt.savefig('daily_simulation_no_power_curve.png')
plt.show()