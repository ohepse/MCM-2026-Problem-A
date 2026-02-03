import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

def model_cpu_gpu_power_clean():
    # 1. 读取数据
    try:
        df = pd.read_csv('aggregated.csv')
    except FileNotFoundError:
        print("错误: 找不到文件 'aggregated.csv'")
        return

    # 2. 定义聚类 (3个CPU + 1个GPU)
    clusters = {
        'Little Core': {'pwr': 'CPU_LITTLE_ENERGY_AVG_UWS', 'freq': 'CPU_LITTLE_FREQ_KHz'},
        'Mid Core':    {'pwr': 'CPU_MID_ENERGY_AVG_UWS',    'freq': 'CPU_MID_FREQ_KHz'},
        'Big Core':    {'pwr': 'CPU_BIG_ENERGY_AVG_UWS',    'freq': 'CPU_BIG_FREQ_KHz'},
        'GPU':         {'pwr': 'GPU_ENERGY_AVG_UWS',        'freq': 'GPU0_FREQ'}
    }

    # 3. 设置绘图布局 (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes_flat = axes.flatten()
    
    # 调整间距，防止标题重叠
    plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.08, wspace=0.25, hspace=0.35)
    
    # 全局字体设置
    plt.rcParams.update({'font.size': 14, 'font.family': 'sans-serif'})

    for idx, (name, cols) in enumerate(clusters.items()):
        ax = axes_flat[idx]
        
        # 检查数据列
        if cols['pwr'] not in df.columns or cols['freq'] not in df.columns:
            ax.text(0.5, 0.5, f'Data Not Found\n{name}', ha='center', va='center', color='red')
            ax.set_title(name)
            continue

        pwr_raw = pd.to_numeric(df[cols['pwr']], errors='coerce')
        freq_raw = pd.to_numeric(df[cols['freq']], errors='coerce')
        data = pd.DataFrame({'pwr': pwr_raw, 'freq': freq_raw}).dropna()
        
        y = data['pwr'].values / 1e6   # W
        x = data['freq'].values / 1000.0 # MHz
        
        mask = x > 0
        x_active = x[mask].reshape(-1, 1)
        y_active = y[mask]
        
        if len(x_active) < 10:
            ax.text(0.5, 0.5, 'Insufficient Data', ha='center')
            continue

        # --- 建模 ---
        poly = PolynomialFeatures(degree=3, include_bias=False)
        x_poly = poly.fit_transform(x_active)
        model = LinearRegression()
        model.fit(x_poly, y_active)
        
        # --- 绘图 ---
        # 1. Measured Data (原始散点)
        ax.scatter(x_active, y_active, alpha=0.15, color='#555555', s=25, label='Measured Data')
        
        # 2. Fitted Curve (拟合曲线)
        x_range = np.linspace(x_active.min(), x_active.max(), 100).reshape(-1, 1)
        y_range = model.predict(poly.transform(x_range))
        ax.plot(x_range, y_range, 'r-', lw=3, label='Fitted Curve')
        
        # --- 装饰 ---
        ax.set_title(f'{name} Power Model', fontsize=20, fontweight='bold', pad=15)
        ax.set_xlabel('Frequency (MHz)', fontsize=16, fontweight='bold')
        ax.set_ylabel('Power (W)', fontsize=16, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # --- 图例 (仅保留两项，不含公式) ---
        ax.legend(loc='upper left', fontsize=14, frameon=True)

    
    plt.show()

if __name__ == "__main__":
    model_cpu_gpu_power_clean()