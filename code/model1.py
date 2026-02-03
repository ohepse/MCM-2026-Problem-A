import numpy as np
import matplotlib.pyplot as plt

def simulate_battery_model():
    # ==========================================
    # 1. 参数定义 (Parameter Definition)
    # ==========================================
    # 电池容量
    Q_capacity_mAh = 4000
    Q_total = Q_capacity_mAh * 3.6  # 转换为库伦 (Coulombs)

    # 等效电路参数 (假设为常数，实际可设为SOC的函数)
    R0 = 0.08    # 欧姆内阻 (Ohm)
    Rp = 0.05    # 极化内阻 (Ohm)
    Cp = 1000    # 极化电容 (Farad) -> 时间常数 tau = Rp*Cp = 50s

    # 开路电压曲线 (OCV Curve) - 简化的非线性函数
    def get_ocv(soc):
        # 模拟锂电池: 3.0V(0%) -> 4.2V(100%)，中间有平坦区
        # 这是一个经验公式，模拟S型曲线
        return 3.2 + 0.8 * soc + 0.2 * np.log(soc + 0.01) - 0.1 * np.log(1.01 - soc)

    # ==========================================
    # 2. 仿真设置 (Simulation Setup)
    # ==========================================
    dt = 1.0                # 时间步长 (秒)
    duration_minutes = 60   # 仿真时长 (分钟)
    total_steps = int(duration_minutes * 60 / dt)
    time = np.arange(0, total_steps * dt, dt)

    # 初始化状态变量数组
    soc = np.zeros(total_steps)
    Up = np.zeros(total_steps)       # 极化电压 (Polarization Voltage)
    Vt = np.zeros(total_steps)       # 端电压 (Terminal Voltage)
    I_load = np.zeros(total_steps)   # 电流 (Current)
    P_load = np.zeros(total_steps)   # 功率负载 (Power Profile)

    # 设定初始状态
    soc[0] = 0.95   # 初始电量 95%
    Up[0] = 0.0     # 初始极化电压为 0

    # ==========================================
    # 3. 定义负载模式 (Load Profile)
    # ==========================================
    # 模拟真实场景：待机 -> 游戏(重负载) -> 视频(中负载) -> 待机
    for t_idx, t in enumerate(time):
        if 600 <= t < 1800:         # 10min - 30min: 玩游戏 (Heavy Load)
            P_load[t_idx] = 8.0     # 8 Watts
        elif 2400 <= t < 3000:      # 40min - 50min: 看视频 (Medium Load)
            P_load[t_idx] = 4.0     # 4 Watts
        else:                       # 待机 (Idle)
            P_load[t_idx] = 0.5     # 0.5 Watts

    # ==========================================
    # 4. 数值积分主循环 (Main Loop)
    # ==========================================
    # 使用欧拉法 (Forward Euler) 解微分方程
    for k in range(total_steps - 1):
        # A. 获取当前状态下的 OCV
        # 注意防止 SOC 越界
        current_soc = max(0.01, min(0.99, soc[k]))
        U_oc = get_ocv(current_soc)

        # B. 解代数方程求电流 I(t)
        # 恒功率约束: P = I * Vt = I * (U_oc - Up - I*R0)
        # 整理得: R0*I^2 - (U_oc - Up)*I + P = 0
        
        # 系数
        a = R0
        b = -(U_oc - Up[k])
        c = P_load[k]

        # 判别式
        delta = b**2 - 4*a*c
        
        if delta < 0:
            print(f"Warning: Power too high at step {k}, voltage collapse!")
            curr_I = (U_oc - Up[k]) / (2*R0) # 甚至无法维持电压，取最大可能电流
        else:
            # 取较小的根 (物理上电流较小的那个解)
            curr_I = (-b - np.sqrt(delta)) / (2*a)
        
        I_load[k] = curr_I

        # C. 计算端电压 Vt
        Vt[k] = U_oc - Up[k] - curr_I * R0

        # D. 更新状态变量 (微分方程离散化)
        # dSOC/dt = -I / Q_total
        dSOC = -curr_I / Q_total
        soc[k+1] = soc[k] + dSOC * dt

        # dUp/dt = I/Cp - Up/(Rp*Cp)
        dUp = (curr_I / Cp) - (Up[k] / (Rp * Cp))
        Up[k+1] = Up[k] + dUp * dt

    # 填充最后一个点的辅助数据
    I_load[-1] = I_load[-2]
    Vt[-1] = Vt[-2]

    # ==========================================
    # 5. 可视化 (Visualization)
    # ==========================================
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # 图1: 功率负载
    ax1.plot(time/60, P_load, 'k-', linewidth=1.5, label='Power Load (W)')
    ax1.fill_between(time/60, P_load, color='gray', alpha=0.2)
    ax1.set_ylabel('Power (W)', fontsize=12)
    ax1.set_title('Simulation of 1st-Order RC Battery Model', fontsize=14)
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--')

    # 图2: 电压响应 (核心物理现象)
    ax2.plot(time/60, Vt, 'b-', linewidth=1.5, label='Terminal Voltage $U_t$')
    # 为了对比，画出 OCV
    ocv_curve = [get_ocv(s) for s in soc]
    ax2.plot(time/60, ocv_curve, 'g--', linewidth=1.5, alpha=0.6, label='Open Circuit Voltage $U_{OC}$')
    ax2.set_ylabel('Voltage (V)', fontsize=12)
    ax2.legend(loc='lower left')
    ax2.grid(True, linestyle='--')
    
    # 标注电压回升现象
    # 找到负载结束的时刻 (30min = 1800s)
    # target_idx = int(1800 / dt) + 60 # 往后一点点
    # if target_idx < total_steps:
    #     ax2.annotate('Recovery (Relaxation)', 
    #                  xy=(target_idx/60, Vt[target_idx]), 
    #                  xytext=(target_idx/60 + 5, Vt[target_idx] + 0.3),
    #                  arrowprops=dict(facecolor='red', shrink=0.05),
    #                  fontsize=10, color='red')

    # 图3: SOC 变化
    ax3.plot(time/60, soc * 100, 'r-', linewidth=2, label='State of Charge (SOC)')
    ax3.set_ylabel('SOC (%)', fontsize=12)
    ax3.set_xlabel('Time (minutes)', fontsize=12)
    ax3.legend(loc='upper right')
    ax3.grid(True, linestyle='--')

    plt.tight_layout()
    plt.show()
    
simulate_battery_model()