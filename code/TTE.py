import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. 核心仿真逻辑 (保持不变)
# ==========================================

def get_ocv_corrected(soc):
    """
    修正后的 OCV 曲线
    100% SoC -> 4.4V
    0% SoC   -> 3.2V
    拟合公式: 3.2 + 0.9*s + 0.3*s^2
    """
    return 3.2 + 0.9 * soc + 0.3 * (soc**2)

def simulate_discharge(power_w, init_soc, capacity_mah=4575):
    """
    模拟恒功率放电
    """
    # 电池参数
    Q_coulomb = capacity_mah * 3.6
    R0 = 0.05
    Rp = 0.03
    Cp = 2000
    tau = Rp * Cp
    cutoff_voltage = 3.0
    
    # 初始化
    dt = 1.0
    soc = init_soc
    up = 0.0
    t = 0.0
    
    time_log = []
    soc_log = []
    
    while soc > 0:
        ocv = get_ocv_corrected(soc)
        
        # 计算电流
        a = R0
        b = -(ocv - up)
        c = power_w
        delta = b**2 - 4*a*c
        
        if delta < 0: break # 电压崩溃
        
        I_load = (-b - np.sqrt(delta)) / (2*a)
        v_term = ocv - up - I_load * R0
        
        if v_term < cutoff_voltage: break
        
        # 更新状态
        soc -= (I_load * dt) / Q_coulomb
        up = up * np.exp(-dt/tau) + I_load * Rp * (1 - np.exp(-dt/tau))
        
        if int(t) % 60 == 0:
            time_log.append(t / 3600.0)
            soc_log.append(soc * 100.0)
            
        t += dt
        
    return time_log, soc_log

# ==========================================
# 2. 修改后的绘图逻辑 (满足新需求)
# ==========================================

def plot_by_initial_soc_final():
    # 定义变量
    init_socs = [1.0, 0.75, 0.50, 0.25]
    scenarios = [
        {'power': 3.87, 'label': 'Heavy Usage(3.87W)', 'color': '#b52024'}, # 红
        {'power': 2.21, 'label': 'Medium Usage(2.21W)',  'color': '#12501d'}, # 绿
        {'power': 1.00, 'label': 'Light Usage(1.00W)',  'color': '#0271bb'}  # 蓝
    ]
    
    # 创建 2x2 的子图布局
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True)
    axes = axes.flatten()
    
    for i, start_soc in enumerate(init_socs):
        ax = axes[i]
        
        # 预先计算该子图下的所有曲线数据，以便确定 X 轴范围
        plot_data = []
        max_time_in_subplot = 0
        
        for scen in scenarios:
            t_data, soc_data = simulate_discharge(scen['power'], start_soc)
            plot_data.append({'scen': scen, 't': t_data, 'soc': soc_data})
            if len(t_data) > 0:
                max_time_in_subplot = max(max_time_in_subplot, t_data[-1])
        
        # 设置 X 轴范围：预留 25% 的空间给右侧的方框
        ax.set_xlim(0, max_time_in_subplot * 1.25)
        ax.set_ylim(-5, 115) # Y轴范围
        
        # 设置标题和标签
        ax.set_title(f'Initial Battery: {int(start_soc*100)}%', fontsize=20, fontweight='bold')
        ax.set_xlabel('Time (Hours)', fontsize=18, fontweight='bold')
        if i % 2 == 0:
            ax.set_ylabel('State of Charge (%)', fontsize=18, fontweight='bold')
            
        ax.grid(True, linestyle='--', alpha=0.4) 
        
        # 绘制曲线和方框
        for k, item in enumerate(plot_data):
            scen = item['scen']
            t_data = item['t']
            soc_data = item['soc']
            
            # 绘制曲线
            ax.plot(t_data, soc_data, linewidth=2.5, color=scen['color'], 
                    label=scen['label'])
            
            if len(t_data) > 0:
                final_time = t_data[-1]
                
                # --- 定位逻辑 ---
                # Y轴: 错开 (5, 15, 25)
                y_pos = 15 
                
                # X轴: 放在右侧空白区域的特定位置，或者相对于终点偏移
                # 为了"居中对齐"且"放在图像内部"，我们设定一个相对偏移量
                # 这里我们让方框中心位于终点右侧一定距离
                x_center = final_time + (max_time_in_subplot * 0.12)
                
                # --- 样式逻辑 ---
                # 1. 圆角方框 + 统一高度 (通过 padding 控制)
                # pad=0.6 保证高度一致且空间充裕
                bbox_props = dict(boxstyle="round,pad=0.6", 
                                  fc="white", 
                                  ec="gray", 
                                  alpha=0.95, 
                                  linewidth=2.5)
                
                # 2. 绘制文字 (ha='center' 实现居中对齐)

                ax.annotate("", 
                            xy=(final_time, 0),          # 箭头尖端
                            xytext=(x_center, y_pos),    # 箭头尾部 (文字中心)
                            arrowprops=dict(arrowstyle="-|>", 
                                            color=scen['color'], 
                                            alpha=0.6, 
                                            linewidth=2.5,    # 加粗
                                            mutation_scale=20 # 箭头变大
                                           ))
                
                ax.text(x_center, y_pos, f'{final_time:.1f}h', 
                        color=scen['color'], fontweight='bold', fontsize=16, 
                        ha='center', va='center', # 文字在坐标点居中
                        bbox=bbox_props)
                
                # 3. 绘制加粗箭头
                # 箭头从文字框边缘(自动计算)指向 (final_time, 0)
                

        # 图例
        if i == 0:
            ax.legend(loc='upper right', fontsize=16, frameon=True, framealpha=1.0)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_by_initial_soc_final()