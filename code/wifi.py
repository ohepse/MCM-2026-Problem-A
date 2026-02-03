import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

df = pd.read_csv('aggregated.csv')

# 1. 数据预处理
# 检查 'TOTAL_DATA_WIFI_BYTES' 是否为累计值
is_monotonic = df['TOTAL_DATA_WIFI_BYTES'].is_monotonic_increasing
# 如果不是单调增加，可能已经是速率；如果是单调增加，则是累计值。
# 从之前的数据看，它不是严格单调的（有时归零），可能是分段累计或就是速率。
# 让我们先画图看看。


# 假设它是速率 (Bytes per sample interval)，直接拟合
X_rate = df[['TOTAL_DATA_WIFI_BYTES']]
y_power = df['WLANBT_ENERGY_AVG_UWS'] 

# 拟合
model = LinearRegression()
model.fit(X_rate, y_power)

# R2 较低 (0.32)，说明简单的线性关系受干扰较大（可能是蓝牙，或者Wi-Fi状态切换的滞后效应）。
# 让我们尝试引入非线性或分段。
# Wi-Fi 芯片通常有 "High Power State" 和 "Low Power State"。
# 画出 散点图 观察分布。

plt.figure(figsize=(8,6))
plt.scatter(df['TOTAL_DATA_WIFI_BYTES'], df['WLANBT_ENERGY_AVG_UWS'], alpha=0.3, s=10)
plt.plot(X_rate, model.predict(X_rate), color='red', label='Linear Fit')
plt.xlabel('Data Throughput (Bytes)',fontsize=16,fontweight='bold')
plt.ylabel('WLAN+BT Power (uW)',fontsize=16,fontweight='bold')
plt.legend()
plt.show()
# 检查是否有明显的两团数据（High/Low states）
# 尝试过滤掉数据量为 0 的点，看看纯传输时的效率
mask_active = df['TOTAL_DATA_WIFI_BYTES'] > 1000 # Ignore minimal background traffic
model_active = LinearRegression()
model_active.fit(df.loc[mask_active, ['TOTAL_DATA_WIFI_BYTES']], df.loc[mask_active, 'WLANBT_ENERGY_AVG_UWS'])

# 另一种假设：如果相关性很低，尝试去掉蓝牙干扰或异常值
# 很多时候 WLANBT 包含蓝牙，如果蓝牙一直在工作，Base Power 会偏高。