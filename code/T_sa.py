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
# 1. Battery Model with Temperature Dependency
# ==========================================
def get_ocv_corrected(soc):
    # Simplified OCV curve: 3.2V (0%) -> 4.4V (100%)
    return 3.2 + 0.9 * soc + 0.3 * (soc**2)

class BatterySimTemp:
    def __init__(self, temp_c, capacity_ref_mah=4575, R0_ref=0.05):
        self.temp_c = temp_c
        
        # Temperature Dependency Model (Arrhenius-like approximations)
        # Reference Temp: 25 C
        T_ref = 298.15 # Kelvin
        T_curr = temp_c + 273.15
        
        # 1. Internal Resistance R0 (Decreases as Temp increases)
        # R = R_ref * exp( E_a / k * (1/T - 1/T_ref) )
        # Simplified factor for demonstration:
        # 0C -> ~1.6x, 25C -> 1.0x, 45C -> ~0.8x
        # Using a simplified exponential decay factor
        self.R0 = R0_ref * np.exp(2500 * (1/T_curr - 1/T_ref))
        
        # 2. Capacity Q (Increases as Temp increases, drops sharply at low temp)
        # 0C -> ~80%, 25C -> 100%, 45C -> ~102%
        if temp_c < 25:
            cap_factor = 1.0 - 0.01 * (25 - temp_c) # Linear drop for simplicity
        else:
            cap_factor = 1.0 + 0.001 * (temp_c - 25)
        
        self.Q_coulomb = (capacity_ref_mah * cap_factor) * 3.6
        
        # Polarization parameters also affected, but keeping constant for clarity of main effects
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
# 2. Temperature Sensitivity Simulation
# ==========================================

load_power = 3.87 # Constant Load (Watts)
temps = [0, 25, 15] # Celsius
colors = ['#4C72B0', '#55A868', '#C44E52'] # Blue (Cold), Green (Nominal), Red (Hot)
labels = ['Cold (0°C)', 'Nominal (25°C)', 'Hot (45°C)']

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8,12), sharex=True)

for temp, col, label in zip(temps, colors, labels):
    sim = BatterySimTemp(temp_c=temp)
    time = []
    voltage = []
    soc_list = []
    curr_t = 0
    dt = 1.0
    
    while True:
        v, i, s = sim.step(load_power, dt)
        if v is None or v < 3.0 or s <= 0:
            break
        
        if curr_t % 60 == 0: # Record every minute
            time.append(curr_t / 60) # Minutes
            voltage.append(v)
            soc_list.append(s * 100)
            
        curr_t += dt
        
    # Plot Voltage
    ax1.plot(time, voltage, color=col, linewidth=3, label=f"{label}")
    ax1.scatter(time[-1], voltage[-1], color=col, s=100, zorder=5)
    
    # Plot SoC
    ax2.plot(time, soc_list, color=col, linewidth=3, label=f"{label}")
    ax2.scatter(time[-1], soc_list[-1], color=col, s=100, zorder=5)
    
    # Drop lines
    ax1.axvline(time[-1], color=col, linestyle=':', alpha=0.5)
    ax2.axvline(time[-1], color=col, linestyle=':', alpha=0.5)

# Style Plot 1: Voltage
ax1.axhline(3.0, color='black', linestyle='--', linewidth=2, label='Cutoff Voltage (3.0V)')
ax1.set_ylabel('Terminal Voltage (V)', fontsize=18)
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.set_ylim(2.8, 4.5)

# Style Plot 2: SoC
ax2.set_ylabel('State of Charge (SoC %)', fontsize=18)
ax2.set_xlabel('Runtime (Minutes)', fontsize=18)
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.set_ylim(0, 105)
ax2.legend(loc='lower left', fontsize=14, frameon=True)

plt.tight_layout()
plt.show()