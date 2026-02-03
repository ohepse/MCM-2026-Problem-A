import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. 手动数据输入区 (MANUAL INPUT DATA)
# 请在这里填写您的设定，其他地方不需要修改
# ==========================================

# --- A. 电池参数 (Pixel 8) ---
BATTERY_CONFIG = {
    'capacity_mah': 4575,    # 电池容量
    'voltage_nom': 3.87,     # 标称电压 (用来算能量 Wh)
}

# --- B. 场景设定 (Scenarios) ---
# 您可以在这里调整三个场景的具体行为
SCENARIOS = {
    'Heavy Gaming': {
        'brightness': 220,       # 0-255
        'cpu_load': 1.0,         # 0.0-1.0 (1.0 = 满载)
        'gpu_power_w': 2.0,      # 手动估算 GPU 功耗 (W)
        'audio_power_w': 0.3,    # 手动估算 音频功耗 (W)
        'wifi_mbps': 1.0,        # WiFi 流量 (MB/s)
        'base_power_w': 0.4      # 系统底噪 (W, High activity)
    },
    'Video Streaming': {
        'brightness': 150,
        'cpu_load': 0.3,         # 硬解，负载较低
        'gpu_power_w': 0.1,      # UI 渲染，很低
        'audio_power_w': 0.2,
        'wifi_mbps': 5.0,        # 高清流媒体
        'base_power_w': 0.2
    },
    'Light Idle': {
        'brightness': 0,
        'cpu_load': 0.02,        # 后台心跳
        'gpu_power_w': 0.0,
        'audio_power_w': 0.0,
        'wifi_mbps': 0.0,
        'base_power_w': 0.15     # Pixel 基带待机
    }
}

# --- C. 建模系数 (Coefficients) ---
# 基于之前的回归分析 (Pixel 8 修正版)
COEFFS = {
    'screen_base': 0.05,
    'screen_slope': 0.0055,      # W per brightness level (高亮屏幕)
    'cpu_max_power': 1.5,        # W (CPU 满载时的功耗估算)
    'wifi_slope': 0.005          # W per MB/s
}

# ==========================================
# 2. 计算逻辑 (Calculation Engine)
# ==========================================

def calculate_scenario_power(params, coeffs):
    """根据输入参数计算各组件功耗"""
    # 1. Screen
    p_screen = coeffs['screen_base'] + coeffs['screen_slope'] * params['brightness']
    if params['brightness'] == 0: p_screen = 0 # 息屏修正
    
    # 2. CPU (简化线性模型: Load * MaxPower)
    p_cpu = params['cpu_load'] * coeffs['cpu_max_power']
    
    # 3. WiFi
    p_wifi = params['wifi_mbps'] * coeffs['wifi_slope']
    
    # 4. Others (Manual)
    p_gpu = params['gpu_power_w']
    p_audio = params['audio_power_w']
    p_base = params['base_power_w']
    
    total = p_screen + p_cpu + p_wifi + p_gpu + p_audio + p_base
    
    return {
        'Total': total,
        'Breakdown': {
            'Screen': p_screen,
            'CPU': p_cpu,
            'GPU': p_gpu,
            'WiFi': p_wifi,
            'Audio': p_audio,
            'System Base': p_base
        }
    }

# ==========================================
# 3. 执行计算与绘图 (Execution)
# ==========================================

def main():
    # 1. 准备数据
    results = {}
    battery_wh = (BATTERY_CONFIG['capacity_mah'] / 1000) * BATTERY_CONFIG['voltage_nom']
    print(f"--- Battery Energy: {battery_wh:.2f} Wh ---\n")

    # 2. 遍历计算
    for name, params in SCENARIOS.items():
        res = calculate_scenario_power(params, COEFFS)
        results[name] = res
        
        # 打印详细数据
        print(f"[{name}] Total Power: {res['Total']:.3f} W")
        print(f"  > TTE (100%): {battery_wh / res['Total']:.2f} Hours")
        # 打印 TTE 表格 (100%, 75%, 50%, 25%)
        print("  > TTE Estimates:")
        for soc in [1.0, 0.75, 0.5, 0.25]:
            energy = battery_wh * soc
            time_h = energy / res['Total']
            print(f"    - {int(soc*100)}% SOC: {time_h:.2f} h ({int(time_h*60)} min)")
        print("-" * 30)

    # 3. 绘制饼状图
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6']
    # 对应: Screen, CPU, GPU, WiFi, Audio, Base
    
    for idx, (name, res) in enumerate(results.items()):
        ax = axes[idx]
        breakdown = res['Breakdown']
        
        # 过滤掉 0 值以便绘图美观
        labels = []
        sizes = []
        for k, v in breakdown.items():
            if v > 0.01: # 忽略极小值
                labels.append(k)
                sizes.append(v)
        
        # 绘制
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                          startangle=140, colors=colors, pctdistance=0.85)
        
        # 环形图样式
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        ax.add_artist(centre_circle)
        
        ax.set_title(f"{name}\n({res['Total']:.2f} W)", fontsize=14, fontweight='bold')
        
        # 优化字体
        plt.setp(texts, size=10)
        plt.setp(autotexts, size=10, weight="bold")

    plt.suptitle(f"Power Consumption Breakdown (Pixel 8)", fontsize=16)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()