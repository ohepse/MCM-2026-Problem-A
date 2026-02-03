### 第一步：确立核心微分方程 (The Governing Equation)

$$SOC(t) = \frac{Q(t)}{Q_{rated}}$$

$$SOC(t) = SOC(t_0) - \frac{1}{Q_n} \int_{t_0}^{t} \eta I(\tau) d\tau,\eta =  1$$

$$\frac{dSOC(t)}{dt} = - \frac{\eta I(t)}{Q_n}$$

这是模型的高级之处，也是区别于简单线性回归的关键。

手机消耗的是**功率 (Power, Watts)**，而不是固定的电流。根据 $P(t) = V(t) \cdot I(t)$，我们得到：

$$I(t) = \frac{P_{total}(t)}{V(t)}$$

这意味着：**当电池电压 $V(t)$ 下降时，为了维持相同的功率（比如玩游戏），电流 $I(t)$ 必须增加。** 这就解释了为什么电量低时，电池似乎消耗得更快（雪崩效应）。

为了求出 $V(t)$，我们需要引入**等效电路 (ECM)**：

**端电压方程：**

$$U_t(t) = U_{OC}(SOC) - U_p(t) - I(t)R_0$$

- $V_{OCV}(SOC)$: **开路电压 (Open Circuit Voltage)**。这是锂电池的固有化学属性，是一个非线性函数（S型曲线）。查表或拟合得到。
- $R_{0}$: **内阻 (Internal Resistance)**。这是物理损耗的来源。
- $U_p$: 瞬态电压（由电容引起），用来模拟电池电压在负载变化后的“回升”现象（Relaxation effect）。

根据图中 $R_p$ 和 $C_p$ 的并联关系，流过电容的电流等于总电流减去流过电阻 $R_p$ 的电流。

$$C_p \frac{dU_p}{dt} = I(t) - \frac{U_p}{R_p}$$

整理得到关于 $U_p$ 的微分方程：

$$\frac{dU_p}{dt} = \frac{1}{C_p} I(t) - \frac{1}{R_p C_p} U_p(t)$$

这是建模中最难的一步。因为手机是**恒功率设备 (Constant Power Load)**，而不是恒流设备。

已知手机功率 $P(t)$（来自屏幕+CPU等），则 $P(t) = U_t(t) \cdot I(t)$。

我们需要把输出方程代入功率公式，解出电流 $I(t)$：

$$P(t) = I(t) \cdot [ U_{OC}(SOC) - U_p(t) - I(t)R_0 ]$$

这依然是一个关于 $I(t)$ 的一元二次方程：

$$R_0 \cdot I(t)^2 - [U_{OC}(SOC) - U_p(t)] \cdot I(t) + P(t) = 0$$

**解出电流 $I(t)$：**

$$I(t) = \frac{[U_{OC}(SOC) - U_p(t)] - \sqrt{[U_{OC}(SOC) - U_p(t)]^2 - 4 R_0 P(t)}}{2 R_0}$$

最终得到：

$$\begin{cases} \frac{dSOC}{dt} = -\frac{I(t)}{Q_{total}} \\ \frac{dU_p}{dt} = \frac{I(t)}{C_p} - \frac{U_p}{R_p C_p} \\ I(t) = \frac{(U_{OC} - U_p) - \sqrt{(U_{OC} - U_p)^2 - 4 R_0 P_{load}}}{2 R_0} \end{cases}$$

------

### 第二步：分解功耗函数 $P_{total}(t)$ (Component Breakdown)

这是模型的灵魂部分。你需要将总电流拆解为几个主要的物理驱动因素，正如题目所暗示的 。

$$P_{total}(t) =P_{base} +P_{screen}(t) + P_{CPU}(t) + P_{wifi}+P_{GPS}+P_{network}(t) + \dots $$

建议为每个部分建立独立的子模型：

1. **基础待机功耗 ($P_{base}$):**

   - 即便手机“看起来空闲”，后台进程和维持通信基带也在耗电 。这可以设为一个常数或通过后台任务数量修正的变量。
   - 30 - 50 mW

2. **屏幕功耗 ($P_{screen}$):**

   - OLED屏的功耗主要取决于显示的内容 和**开启状态** ($On/Off$)。
   - 模型假设：$ P_{screen}(t) = B(t) \cdot (k_rR + k_bB + k_gG)+C$。
   - 其中 $B(t) \in [0,100]$ 是 亮度，$R,G,B \in [0.255]$
   - M. Dong and L. Zhong, "Chameleon: A Color-Adaptive Web Browser for Mobile OLED Displays," in IEEE Transactions on Mobile Computing, vol. 11, no. 5, pp. 724-738, May 2012, doi: 10.1109/TMC.2012.40.

3. **处理器功耗 ($P_{CPU/GPU}$):**

   * 功率正比于处理器频率和电压的平方

   - 假定 $P = C \cdot V^2 \cdot f$（频率）。
   - 电压与频率成正相关，但是存在启动电压，即$$V(f) = V_{min} + \alpha \cdot f$$，所以选择用三项式来拟合处理器的功耗。

   $$P(f) \propto f \cdot (V_{min} + \alpha f)^2$$

   $$P(f) \propto f \cdot (V_{min}^2 + 2\alpha V_{min} f + \alpha^2 f^2)$$

   $$P(f) \approx \underbrace{k_1 f}_{\text{Vmin主导的低频项}} + \underbrace{k_2 f^2}_{\text{交叉项}} + \underbrace{k_3 f^3}_{\text{理想DVS项}}$$

   * $P = c_0 + c_1 f + c_2 f^2 + c_3 f^3$
   * Power_Management_and_Dynamic_Voltage_Scaling_Myths论文

4. **GPS功耗**

   * GPS 的功耗主要取决于它是处于“活动（Active）”模式还是“睡眠（Sleep）”模式 。虽然卫星数量和信号强度在物理上会有影响，但在系统级功耗建模中，它们的影响微乎其微，可以忽略 。
   * $P_{GPS}=P_1 \cdot \delta(t)+P_{sleep}  $
   * 

5. Wi-Fi 模块的功耗不仅取决于数据量，还取决于数据包的发送频率。

   - **状态逻辑**：Wi-Fi 接口主要分为“低功耗（Low-power）”和“高功耗（High-power）”两种基本状态 。

     - **状态切换阈值**：决定进入高功耗状态的不是数据流量（Bit rate），而是**包率（Packet rate）** 。

       * 当每秒传输/接收超过 **15 个数据包**时，进入高功耗模式 。

       - 当每秒数据包低于 **8 个**时，返回低功耗模式（存在滞后效应/Hysteresis） 。

   - **高功耗状态下的公式**：

     一旦进入高功耗状态，功耗与数据传输速率（$R_{data}$）呈线性关系，同时受链路速率（$R_{channel}$，如 54Mbps, 11Mbps）影响：

     $$P_{Wi-Fi(High)} = P_{base} + \beta_{cr}(R_{channel}) \times R_{data}$$

     - $P_{base}$：高功耗状态的基础功耗（文中约为 710 mW） 。

     - $\beta_{cr}$：与当前信道速率相关的系数，信道质量越差（速率越低），传输单位数据的能耗越高 。

    - **低功耗状态**：约为 20 mW 。

   * $$P_{wifi}\begin{cases}P_{base} + \beta_{cr}(R_{channel}) \times R_{data},high\\P_{low},low \end{cases}$$

7. **蜂窝网络功耗**

   * 与其状态有关
   * $$P_{network}\begin{cases}P_{idle},state = IDLE \\ P_{fach},state = FACH \\ P_{DCH},state=DCH\end{cases}$$

   **三个核心状态** ：

   1. **IDLE (空闲)**：仅接收寻呼信息，功耗极低（约 10 mW） 。
   2. **CELL_FACH (前向接入信道)**：共享信道，用于低速数据传输。功耗中等（约 401 mW） 
   3. **CELL_DCH (专用信道)**：专用高速信道，用于大量数据传输。功耗最高（约 570 mW） 。

8. **论文参考**

   Accurate_online_power_estimation_and_automatic_battery_behavior_based_power_model_generation_for_smartphones

   P. K. D. Pramanik *et al*., "Power Consumption Analysis, Measurement, Management, and Issues: A State-of-the-Art Review of Smartphone Battery and Energy Usage," in *IEEE Access*, vol. 7, pp. 182113-182172, 2019, doi: 10.1109/ACCESS.2019.2958684. 

------

### 第三步：引入环境与老化修正 (Refining Constraints)

题目特别强调了**温度 (Temperature)** 和 **老化 (Aging)** 。不要把它们忽略。

1. 改进：将时间换为循环次数

​	$$\begin{equation*} Q_{\mathrm{ loss}}(N,T,\text {SoC}) = Ae^{B\cdot \text {SoC}}\cdot e^{\frac {-E_{a}+C\cdot \text {SOC}}{kT}}N^{z} \end{equation*}$$

​	修正因子 $\eta = \frac{Q_{rated}-Q_{loss}}{Q_{rated}}$

1. **论文参考**

   W. Vermeer, G. R. Chandra Mouli and P. Bauer, "A Comprehensive Review on the Characteristics and Modeling of Lithium-Ion Battery Aging," in *IEEE Transactions on Transportation Electrification*, vol. 8, no. 2, pp. 2205-2232, June 2022, doi: 10.1109/TTE.2021.3138357. 

------

### 第四步：最终模型

$$\begin{cases} \frac{dSOC}{dt} = -\frac{I(t)}{\eta Q_{rated}} \\ \frac{dU_p}{dt} = \frac{I(t)}{C_p} - \frac{U_p}{R_p C_p} \\ I(t) = \frac{(U_{OC} - U_p) - \sqrt{(U_{OC} - U_p)^2 - 4 R_0 P_{total}}}{2 R_0} \\ P_{total}(t) =P_{base} +P_{screen}(t) + P_{CPU}(t) + P_{wifi}+P_{GPS}+P_{network}(t) + \dots \end{cases}$$

