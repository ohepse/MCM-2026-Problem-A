import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Style settings
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
# 1. Battery Model (Thevenin)
# ==========================================
def get_ocv_corrected(soc):
    # Simplified OCV curve
    return 3.2 + 0.9 * soc + 0.3 * (soc**2)

class BatterySimLoad:
    def __init__(self, capacity_mah=4575): # Using 4575mAh as per earlier snippets
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
        
        # Solving Quadratic for Current I: R0*I^2 - (OCV-Up)*I + P = 0
        a = self.R0
        b = -(ocv - self.up)
        c = power_w
        delta = b**2 - 4*a*c
        
        if delta < 0:
            return None, None, None # Voltage Collapse
            
        I_load = (-b - np.sqrt(delta)) / (2*a)
        v_term = ocv - self.up - I_load * self.R0
        
        if v_term < self.cutoff_voltage or self.soc <= 0:
            return v_term, I_load, 0.0 # Empty/Cutoff
            
        # Update State
        self.soc -= (I_load * dt) / self.Q_coulomb
        self.up = self.up * np.exp(-dt/self.tau) + I_load * self.Rp * (1 - np.exp(-dt/self.tau))
        
        return v_term, I_load, self.soc

# ==========================================
# 2. OAT Sensitivity Analysis: Load Power
# ==========================================

# Defined Power Levels
power_values = [0.8, 0.9, 1.0, 1.1, 1.2]
perturbation_labels = ["-100%", "-50%", "0% (Baseline)", "+50%", "+100%"]
labels = [f"{label} ($P={val}W$)" for label, val in zip(perturbation_labels, power_values)]

# Colors: Coolwarm (Blue -> Red)
# Blue (Low Power) -> Red (High Power)
cmap = cm.get_cmap('coolwarm', 5)
colors = [cmap(i) for i in range(5)]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))

for val, label, col in zip(power_values, labels, colors):
    sim = BatterySimLoad()
    time = []
    voltage = []
    soc_list = []
    curr_t = 0
    dt = 1.0 # 1 second resolution for high load accuracy
    
    while True:
        v, i, s = sim.step(val, dt)
        
        if v is None or v < 3.0 or s <= 0:
            break
        
        # Record every minute
        if curr_t % 60 == 0:
            time.append(curr_t / 60) # Minutes
            voltage.append(v)
            soc_list.append(s * 100)
            
        curr_t += dt
    
    # Plot Voltage
    ax1.plot(time, voltage, color=col, linewidth=3, label=label)
    ax1.scatter(time[-1], voltage[-1], color=col, s=100)
    
    # Plot SoC
    ax2.plot(time, soc_list, color=col, linewidth=3, label=label)
    ax2.scatter(time[-1], soc_list[-1], color=col, s=100)

# Style Plot 1
ax1.axhline(3.0, color='black', linestyle='--', linewidth=2, label='Cutoff Voltage (3.0V)')
ax1.set_ylabel('Terminal Voltage (V)', fontsize=18)
ax1.grid(True, linestyle='--', alpha=0.5)

ax1.set_ylim(2.8, 4.5)

# Style Plot 2
ax2.set_ylabel('State of Charge (SoC %)', fontsize=18)
ax2.set_xlabel('Runtime (Minutes)', fontsize=18)
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.set_ylim(0, 105)
ax2.legend(loc='lower left', fontsize=14, frameon=True)

plt.tight_layout()
plt.show()