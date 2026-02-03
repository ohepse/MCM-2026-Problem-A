import numpy as np
import matplotlib.pyplot as plt

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

class BatterySim:
    def __init__(self, R0=0.05, capacity_mah=4575):
        self.Q_coulomb = capacity_mah * 4.4
        self.R0 = R0 # This is the variable we sensitivity test
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
# 2. Sensitivity Analysis Simulation
# ==========================================
load_power = 3.87 # High load (Watts)
R0_values = [0.05, 0.11, 0.15] 
colors = ['#55A868', '#4C72B0', '#C44E52'] # Green, Blue, Red
labels = ['New Battery ($R_0=0.05\Omega,0times$)', 'Used Battery ($R_0=0.11\Omega$,5000times)', 'Aged Battery ($R_0=0.12\Omega$,10000times)']

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 12), sharex=True)

for r0, col, label in zip(R0_values, colors, labels):
    sim = BatterySim(R0=r0)
    time_min = []
    voltage_list = []
    soc_list = []
    curr_t = 0
    dt = 1.0
    
    while True:
        v, i, s = sim.step(load_power, dt)
        if v is None or v < 3.0 or s <= 0:
            break
        
        if curr_t % 60 == 0: # Record every minute
            time_min.append(curr_t / 60)
            voltage_list.append(v)
            soc_list.append(s * 100) # Convert to %
            
        curr_t += dt
        
    # Plot Voltage
    ax1.plot(time_min, voltage_list, color=col, linewidth=3, label=f"{label}")
    # Mark endpoint on Voltage
    ax1.scatter(time_min[-1], voltage_list[-1], color=col, s=100, zorder=5)
    ax1.axvline(time_min[-1], color=col, linestyle=':', alpha=0.5)
    
    # Plot SoC
    ax2.plot(time_min, soc_list, color=col, linewidth=3, label=f"{label}")
    # Mark endpoint on SoC
    ax2.scatter(time_min[-1], soc_list[-1], color=col, s=100, zorder=5)
    ax2.axvline(time_min[-1], color=col, linestyle=':', alpha=0.5)

# Style Plot 1: Voltage
ax1.set_ylabel('Terminal Voltage (V)', fontsize=18)
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.axhline(3.0, color='black', linestyle='--', linewidth=2, label='Cutoff (3.0V)')
ax1.set_ylim(2.8, 4.5)

# Style Plot 2: SoC
ax2.set_ylabel('State of Charge (%)', fontsize=18)
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.set_xlabel('Time (Minutes)', fontsize=18)
ax2.set_ylim(0, 105)
ax2.legend(loc='lower left', fontsize=14, frameon=True)

plt.tight_layout()
plt.show()