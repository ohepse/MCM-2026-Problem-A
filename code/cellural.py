import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# 1. Load Data
try:
    df = pd.read_csv('aggregated.csv')
    
    # Identify the correct column for Cellular Power
    # Based on the snippet, it might be 'CELLULAR_ENERGY_AVG_UWS'
    target_col = None
    for col in df.columns:
        if 'CELLULAR' in col.upper() and 'ENERGY' in col.upper():
            target_col = col
            break
            
    if target_col:
        print(f"Target Column Found: {target_col}")
        
        # 2. Process Data
        # Convert uWs to W (Assuming 1s interval or simply treating as mean power in uW)
        # 1 uW = 1e-6 W
        # If the column contains non-numeric data (e.g. errors), coerce them
        y_data = pd.to_numeric(df[target_col], errors='coerce')
        y_data = y_data.dropna()
        
        # Convert to Watts
        y_data_w = y_data /1e3
        
        x_data = y_data.index # Data ID
        
        # 3. Calculate Stats
        variance = y_data_w.var()
        mean_val = y_data_w.mean()
        
        # 4. Plot
        plt.figure(figsize=(12, 8))
        
        # Style settings
        plt.rcParams.update({
            'font.size': 16,
            'font.weight': 'bold',
            'axes.labelweight': 'bold',
            'axes.titleweight': 'bold',
            'figure.titleweight': 'bold',
            'xtick.labelsize': 14,
            'ytick.labelsize': 14
        })
        
        plt.scatter(x_data, y_data_w, 
                   alpha=0.4, 
                   color='#C44E52', # Muted Red
                   s=30, 
                   edgecolors='none',
                   label='Cellular Data')
        
        # Add Variance Box
        stats_text = (
            f"Variance ($\sigma^2$): {variance:.6f}\n"
            f"Mean ($\mu$): {mean_val:.4f} mW"
        )
        props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='#C44E52')
        plt.gca().text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, fontsize=16,
                verticalalignment='top', bbox=props)
        
        plt.axhline(y=mean_val-2*math.sqrt(variance), color='grey', linestyle='--', linewidth=2, label='Concentration Interval')
        plt.axhline(y=mean_val+2*math.sqrt(variance), color='grey', linestyle='--', linewidth=2)
        
        plt.xlabel('Data Sample', fontsize=18)
        plt.ylabel('Cellular Power (mW)', fontsize=18)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend(loc='upper right', fontsize=14)
        
        plt.tight_layout()
        plt.show()
        
    else:
        print("Could not find a column with 'CELLULAR' and 'ENERGY' in its name.")
        
except Exception as e:
    print(f"An error occurred: {e}")