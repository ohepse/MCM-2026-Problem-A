import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. 基础仿真模型 (适配灵敏度分析)
# ==========================================

def run_simulation(params):
    """
    运行单次仿真，返回 TTE (小时)
    params: 包含所有物理参数的字典
    """
    # 提取参数
    capacity_coulomb = params['capacity_mah'] * 3.6
    r0 = params['r0']
    rp = 0.03
    cp = 2000
    tau = rp * cp
    
    # 负载功率 (假设一个恒定的混合负载用于基准测试)
    # 例如：屏幕 + CPU + 底噪
    p_load = params['p_base'] + params['p_screen_coeff'] * 150 + 1.0 # 150亮度 + 1W CPU
    
    cutoff = 3.0
    dt = 1.0
    soc = 1.0
    up = 0.0
    t = 0.0
    
    # 简单的 OCV 曲线
    def get_ocv(s):
        return 3.2 + 0.9*s + 0.3*s**2
    
    while soc > 0:
        ocv = get_ocv(soc)
        
        # 计算电流
        a = r0
        b = -(ocv - up)
        c = p_load
        delta = b**2 - 4*a*c
        
        if delta < 0: break # 电压崩溃
        
        i_load = (-b - np.sqrt(delta)) / (2*a)
        v_term = ocv - up - i_load * r0
        
        if v_term < cutoff: break
        
        # 更新
        soc -= (i_load * dt) / capacity_coulomb
        up = up * np.exp(-dt/tau) + i_load * rp * (1 - np.exp(-dt/tau))
        t += dt
        
    return t / 3600.0 # 返回小时

# ==========================================
# 2. 灵敏度分析主逻辑
# ==========================================

def sensitivity_analysis():
    # 1. 定义基准参数 (Baseline)
    baseline_params = {
        'capacity_mah': 4575.0,
        'r0': 0.05,
        'p_base': 0.4,           # 系统底噪
        'p_screen_coeff': 0.005, # 屏幕系数
        'temp_factor': 1.0       # 温度影响因子 (仅作为演示参数)
    }
    
    # 计算基准结果
    base_tte = run_simulation(baseline_params)
    print(f"基准 TTE: {base_tte:.4f} hours")
    
    # 2. 定义要分析的变量和扰动范围 (+/- 10%)
    # Label: (Param_Key, Display_Name)
    variables = [
        ('capacity_mah', 'Battery Capacity ($Q$)'),
        ('r0', 'Internal Resistance ($R_0$)'),
        ('p_base', 'Base Power ($P_{base}$)'),
        ('p_screen_coeff', 'Screen Efficiency ($k_{scr}$)')
    ]
    
    perturbation = 0.10 # 10% 变化
    
    results = []
    
    print("\n--- 灵敏度分析结果 ---")
    for key, label in variables:
        # High Case (+10%)
        p_high = baseline_params.copy()
        p_high[key] = p_high[key] * (1 + perturbation)
        tte_high = run_simulation(p_high)
        
        # Low Case (-10%)
        p_low = baseline_params.copy()
        p_low[key] = p_low[key] * (1 - perturbation)
        tte_low = run_simulation(p_low)
        
        # 计算变化率
        delta_high = (tte_high - base_tte) / base_tte * 100
        delta_low = (tte_low - base_tte) / base_tte * 100
        
        # 计算灵敏度系数 (平均)
        sensitivity_index = (abs(delta_high) + abs(delta_low)) / 2 / (perturbation * 100)
        
        print(f"{label}: Low={delta_low:.2f}%, High={delta_high:.2f}% | Sensitivity={sensitivity_index:.2f}")
        
        results.append({
            'label': label,
            'low': delta_low,
            'high': delta_high
        })
        
    # ==========================================
    # 3. 绘制龙卷风图 (Tornado Plot)
    # ==========================================
    labels = [r['label'] for r in results]
    lows = [r['low'] for r in results]
    highs = [r['high'] for r in results]
    
    y_pos = np.arange(len(labels))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 绘制条形
    rects_low = ax.barh(y_pos, lows, align='center', color='#1f77b4', label='-10% Input')
    rects_high = ax.barh(y_pos, highs, align='center', color='#d62728', label='+10% Input')
    
    # 装饰
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=12)
    ax.invert_yaxis()  # 让影响最大的在上面（通常需要先排序，这里暂按顺序）
    ax.set_xlabel('Change in TTE (%)', fontsize=12)
    ax.set_title(f'Sensitivity Analysis (Tornado Plot)\nBaseline TTE = {base_tte:.2f}h', fontsize=14)
    ax.axvline(0, color='black', linewidth=0.8)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    ax.legend()
    
    # 添加数值标签
    for i, (l, h) in enumerate(zip(lows, highs)):
        ax.text(l - 0.5 if l < 0 else l + 0.5, i, f'{l:.1f}%', va='center', ha='right' if l < 0 else 'left', color='#1f77b4', fontweight='bold')
        ax.text(h + 0.5 if h > 0 else h - 0.5, i, f'{h:.1f}%', va='center', ha='left' if h > 0 else 'right', color='#d62728', fontweight='bold')
        
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    sensitivity_analysis()