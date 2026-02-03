import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Load the dataframe
df = pd.read_csv('consumption.csv', index_col=0)

# Columns to include in the pie chart
cols_to_plot = ['screen', 'CPU', 'GPU', 'network', 'audio', 'base']

# Scenarios to plot
scenarios = ['heavy', 'medium', 'light']

# Create subplots
fig, axes = plt.subplots(1, 3, figsize=(20, 7))

colors = [
    '#EDA68F', # Screen: Muted Coral (Soft, warm)
    '#A1C3D1', # CPU: Muted Sky Blue (Calm, tech)
    '#B3D4C4', # GPU: Sage Green (Natural, soft)
    '#9FA8DA', # Network: Soft Indigo (Stable but light)
    '#E1BEE7', # Audio: Pale Purple (Gentle)
    '#CFD8DC'  # Base: Light Blue-Gray (Neutral background)
]
# Map colors to columns to ensure consistency across charts
color_map = dict(zip(cols_to_plot, colors))

for i, scenario in enumerate(scenarios):
    ax = axes[i]
    if scenario in df.index:
        data = df.loc[scenario, cols_to_plot]
        
        # Filter out zero values
        data_filtered = data[data > 0]
        
        # Get corresponding colors for the filtered data
        current_colors = [color_map[col] for col in data_filtered.index]
        
        # Plot Donut chart (using wedgeprops for width)
        wedges, texts, autotexts = ax.pie(
            data_filtered, 
            labels=None, 
            autopct='%1.1f%%', 
            startangle=140, 
            colors=current_colors,
            pctdistance=0.8, # Adjust for donut
            wedgeprops=dict(width=0.4, edgecolor='w'), # Creates the hole
            textprops={'fontsize': 16, 'weight': 'bold'} # General text props
        )
        
        ax.axis('equal')  
        
        # Title in the center
        total_power = df.loc[scenario, 'total']
        center_text = f"{scenario.capitalize()}\nUsage\n{total_power:.2f} W"
        ax.text(0, 0, center_text, ha='center', va='center', fontsize=18, fontweight='bold')
        
        # Improve autotexts (percentages) readability specific settings
        plt.setp(autotexts, size=16, weight="bold")
        
    else:
        ax.axis('off')

# Create a unified legend for the whole figure
legend_handles = [mpatches.Patch(color=color_map[col], label=col) for col in cols_to_plot]

# Place legend at the lower center
leg = fig.legend(handles=legend_handles, 
           loc='lower center', 
           ncol=len(cols_to_plot), 
           fontsize=16, # Legend font size
           bbox_to_anchor=(0.5, 0.02))

# Set legend text to bold
for text in leg.get_texts():
    text.set_weight('bold')


plt.subplots_adjust(bottom=0.15, top=0.9) 
plt.show()