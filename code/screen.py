import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt

def evaluate_oled_model_r2():
    # 1. Load Data
    df = pd.read_csv('aggregated.csv')
    
    # 2. Preprocessing
    # Target: Display Power in Watts (assuming UWS is micro-watt-seconds per second? No, it's Energy AVG UWS. 
    # Usually Energy AVG UWS means Average Energy in Micro-Watt-Seconds (Joules/1e6) over a duration? 
    # Wait, the column name is 'Display_ENERGY_AVG_UWS'. If it's average power, it might be uW. 
    # Let's assume it represents power in uW (micro-watts) based on typical values.
    # Let's check the magnitude. If it's ~1e5 to 1e6, that's 0.1W to 1W, which is reasonable for a phone screen.
    
    y = df['Display_ENERGY_AVG_UWS'].values / 1e6 # Convert uW to W
    
    # Features
    # Normalize Brightness (0-255 -> 0-1) assuming max is 255. Let's check max first.
    max_bright = df['Brightness'].max()
    if max_bright == 0: max_bright = 1 # Avoid division by zero
    
    B = df['Brightness'].values / max_bright
    R = df['RougeMesuré'].values
    G = df['VertMesuré'].values
    Bleu = df['BleuMesuré'].values
    
    # Construct Interaction Features: P ~ B * (kr*R + kg*G + kb*Bleu)
    # So predictors are B*R, B*G, B*Bleu
    X = np.column_stack((B * R, B * G, B * Bleu))
    
    # 3. Fit Model
    model = LinearRegression(fit_intercept=True) # Intercept represents static power
    model.fit(X, y)
    y_pred = model.predict(X)
    
    # 4. Calculate R^2
    r2 = r2_score(y, y_pred)
    
    # 5. Output Results
    print("-" * 30)
    print("OLED Screen Power Model Evaluation")
    print("-" * 30)
    print(f"R-squared (R^2): {r2:.4f}")
    print(f"Static Power (Intercept): {model.intercept_:.4f} W")
    print(f"Coefficients (W per pixel intensity):")
    print(f"  k_r (Red):   {model.coef_[0]:.8f}")
    print(f"  k_g (Green): {model.coef_[1]:.8f}")
    print(f"  k_b (Blue):  {model.coef_[2]:.8f}")
    
    # 6. Visualization
    plt.figure(figsize=(8, 6))
    plt.scatter(y, y_pred, alpha=0.5, color='purple', label='Data Points')
    
    # Perfect fit line
    min_val = min(y.min(), y_pred.min())
    max_val = max(y.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Fit')
    
    plt.xlabel('Measured Power (W)',fontsize=16,fontweight='bold')
    plt.ylabel('Predicted Power (W)',fontsize=16,fontweight='bold')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('oled_model_r2.png')
    plt.show()
    
    return r2

evaluate_oled_model_r2()

