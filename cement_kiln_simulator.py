import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Constants
fuel_heat_value = 32000  # kJ/kg
specific_heat = 1.0      # kJ/kg·°C
heat_loss_coeff = 0.001  # proportional heat loss factor
ambient_temp = 30        # °C
co2_per_kg_fuel = 3.17   # kg CO2/kg coal

st.title("Cement Kiln Process Simulator")
st.sidebar.header("Input Parameters")

# Sidebar inputs
fuel_rate = st.sidebar.slider("Fuel Rate (kg/hr)", 100, 1000, 500)
motor_speed = st.sidebar.slider("Motor Speed (RPM)", 0.5, 5.0, 2.5, 0.1)
feed_rate = st.sidebar.slider("Feed Rate (kg/hr)", 500, 3000, 1200, 100)
temp_setpoint = st.sidebar.slider("Temperature Setpoint (°C)", 1000, 1500, 1350, 10)
Kp = st.sidebar.slider("PID Proportional Gain (Kp)", 0.0, 5.0, 1.0, 0.1)
Ki = st.sidebar.slider("PID Integral Gain (Ki)", 0.0, 1.0, 0.1, 0.01)
Kd = st.sidebar.slider("PID Derivative Gain (Kd)", 0.0, 1.0, 0.05, 0.01)

# Derived values
kiln_mass = feed_rate * 0.2
residence_time = 30 / motor_speed
efficiency_factor = min(1.0, residence_time / 30)

# PID controller
def pid_control(error, integral, derivative):
    return Kp * error + Ki * integral + Kd * derivative

# Simulation loop with PID
time = np.linspace(0, 3600, 1000)
dt = time[1] - time[0]
temperature = [400]
integral = 0
prev_error = temp_setpoint - temperature[0]

for t in time[1:]:
    error = temp_setpoint - temperature[-1]
    integral += error * dt
    derivative = (error - prev_error) / dt
    control_signal = pid_control(error, integral, derivative)

    fuel_rate_adjusted = max(100, min(1000, fuel_rate + control_signal))
    heat_input_kjs = fuel_rate_adjusted * fuel_heat_value / 3600
    effective_heat_input = heat_input_kjs * efficiency_factor

    heat_loss = heat_loss_coeff * (temperature[-1] - ambient_temp)
    dTdt = (effective_heat_input - heat_loss) / (kiln_mass * specific_heat)
    temperature.append(temperature[-1] + dTdt * dt)
    prev_error = error

temperature = np.array(temperature)
final_temp = temperature[-1]

# Quality
if final_temp >= 1350:
    quality = "✅ Good Clinker Formation"
elif final_temp >= 1200:
    quality = "⚠️ Partial Sintering"
else:
    quality = "❌ Poor Quality"

# CO2 emissions
co2_emitted = fuel_rate * co2_per_kg_fuel  # kg/hr

# Plot temperature
st.subheader("Temperature Profile")
fig, ax = plt.subplots()
ax.plot(time / 60, temperature)
ax.set_xlabel("Time (minutes)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Kiln Temperature Over Time")
ax.grid(True)
st.pyplot(fig)

# Results
st.subheader("Results")
st.write(f"**Final Temperature:** {final_temp:.2f} °C")
st.write(f"**Estimated Product Quality:** {quality}")
st.write(f"**CO2 Emissions:** {co2_emitted:.2f} kg/hr")

# Savings estimate
baseline_fuel = 700
baseline_heat = baseline_fuel * fuel_heat_value / 3600
baseline_temp = (baseline_heat / (kiln_mass * specific_heat)) + ambient_temp
savings = (baseline_fuel - fuel_rate) * 330 * 24  # kg/year
co2_saved = savings * co2_per_kg_fuel
money_saved = savings * 15  # assuming $15/ton

st.subheader("Efficiency Estimate")
st.write(f"**Annual Fuel Saved:** {savings:.0f} kg/year")
st.write(f"**CO2 Reduction:** {co2_saved:.0f} kg/year")
st.write(f"**Estimated Money Saved:** ${money_saved:.2f} /year")
