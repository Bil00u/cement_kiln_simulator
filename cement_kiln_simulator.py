import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- Page Configuration ---
st.set_page_config(page_title="Cement Production Simulator", layout="wide")

# --- Top Controls ---
ctrl_cols = st.columns([1,1,1,1,1,1])
start_btn = ctrl_cols[0].button("▶️ Start")
stop_btn = ctrl_cols[1].button("⏹ Stop")
reset_btn = ctrl_cols[2].button("🔄 Reset")
mode = ctrl_cols[3].selectbox("Mode", ["Automatic", "Manual"])
radius = ctrl_cols[4].slider("Radius (m)", 3.0, 6.0, 5.0, 0.5)
length = ctrl_cols[5].slider("Length (m)", 40.0, 100.0, 80.0, 5.0)

# --- Header ---
st.title("🏭 Cement Production Simulator Kiln & The Smart Factory 🏭")
st.subheader("👷 Bilal El Barbir & Faisal Adam Reda 👷")

# --- Description ---
with st.expander("📝 Description", expanded=True):
    st.write(
        """
        **Features:**
        - Rotary kiln with customizable dimensions (radius & length).
        - Two modes: Automatic (PID) or Manual control.
        - PID sliders for Kp, Ki, Kd.
        - Real-time 3D kiln rotation.
        - Live multi-trend chart: Temperature, Error, Control Signal, CO₂ Emissions.
        - Metric gauges: Temperature, Quality, CO₂ Emissions/hr.
        - Start, Stop, Reset buttons.
        """
    )

# --- Sidebar Parameters ---
fuel_rate_base = st.sidebar.slider("Base Fuel Rate (kg/hr)", 100, 1500, 600)
motor_speed = st.sidebar.slider("Motor Speed (RPM)", 0.5, 10.0, 3.0, 0.1)
feed_rate = st.sidebar.slider("Feed Rate (kg/hr)", 500, 5000, 1500, 100)
temp_setpoint = st.sidebar.slider("Temp Setpoint (°C)", 800, 1600, 1400, 10)
Kp = st.sidebar.slider("Kp", 0.0, 20.0, 5.0, 0.1)
Ki = st.sidebar.slider("Ki", 0.0, 5.0, 0.5, 0.01)
Kd = st.sidebar.slider("Kd", 0.0, 5.0, 0.1, 0.01)

# --- Initialize Session State ---
if 'running' not in st.session_state:
    st.session_state.running = False
if reset_btn or 't' not in st.session_state:
    st.session_state.update({
        't': 0.0,
        'temps': [],
        'errors': [],
        'controls': [],
        'co2s': [],
        'times': [],
        'integral': 0.0,
        'prev_error': 0.0
    })
if start_btn:
    st.session_state.running = True
if stop_btn:
    st.session_state.running = False

# --- Physical Constants ---
heat_val = 32000       # kJ/kg
spec = 1.0             # kJ/kg·°C
loss_coef = 0.001      # heat loss factor
amb_temp = 30          # °C
co2_factor = 3.17      # kg CO₂ per kg fuel
mass = np.pi * radius**2 * length * 1200  # kg

dt = 1.0  # second step

# --- Layout Placeholders ---
viz_col, chart_col = st.columns([1, 2])
gauge_cols = st.columns(3)
with viz_col:
    kiln_vis = st.empty()
with chart_col:
    trend_vis = st.empty()

# --- Simulation Loop ---
while st.session_state.running and st.session_state.t <= 3600:
    t = st.session_state.t
    # Current temp
    T = st.session_state.temps[-1] if st.session_state.temps else amb_temp

    # Control calculation
    if mode == 'Automatic':
        error = temp_setpoint - T
        st.session_state.integral += error * dt
        derivative = (error - st.session_state.prev_error) / dt
        control = Kp * error + Ki * st.session_state.integral + Kd * derivative
        st.session_state.prev_error = error
        fuel_rate = np.clip(fuel_rate_base + control, 100, 1500)
    else:
        error = 0.0
        control = 0.0
        fuel_rate = fuel_rate_base

    # Temperature update
    heat_in = fuel_rate * heat_val / 3600
    loss = loss_coef * (T - amb_temp)
    cooling = feed_rate * spec * (T - amb_temp) / mass
    dT = (heat_in - loss - cooling) / (mass * spec)
    T += dT * dt

    # CO2 calculation
    co2 = fuel_rate * co2_factor

    # Record data
    st.session_state.temps.append(T)
    st.session_state.errors.append(error)
    st.session_state.controls.append(control)
    st.session_state.co2s.append(co2)
    st.session_state.times.append(t/60)
    st.session_state.t += dt

    # 3D Kiln Visualization
    theta = np.linspace(0, 2 * np.pi, 100)
    z = np.linspace(0, length, 100)
    angle = motor_speed * 2 * np.pi / 60 * t
    X = radius * np.cos(theta + angle)
    Y = radius * np.sin(theta + angle)
    fig1 = plt.figure(figsize=(4, 3))
    ax1 = fig1.add_subplot(111, projection='3d')
    ax1.plot_surface(X, Y, z[:, None], color='gray', alpha=0.7)
    ax1.axis('off')
    kiln_vis.pyplot(fig1)

    # Trend Chart DataFrame
    df = pd.DataFrame({
        'Temp (°C)': st.session_state.temps,
        'Error (°C)': st.session_state.errors,
        'Control (kg/hr)': st.session_state.controls,
        'CO₂ (kg/hr)': st.session_state.co2s
    }, index=st.session_state.times)
    trend_vis.line_chart(df)
    time.sleep(0.1)

# --- Final Metrics ---
final_temp = st.session_state.temps[-1] if st.session_state.temps else amb_temp
quality = (
    "✅ Good" if final_temp >= temp_setpoint else
    "⚠️ Partial" if final_temp >= temp_setpoint - 150 else
    "❌ Poor"
)
final_co2 = st.session_state.co2s[-1] if st.session_state.co2s else 0.0

gauge_cols[0].metric("Temperature", f"{final_temp:.1f} °C", delta=f"{final_temp - temp_setpoint:.1f}")
gauge_cols[1].metric("Quality", quality)
gauge_cols[2].metric("CO₂ Emissions/hr", f"{final_co2:.1f} kg")

# --- Auto-Refresh ---
if st.session_state.running:
    st.experimental_rerun()
