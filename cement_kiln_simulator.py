import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint
import matplotlib.colors as mcolors

# Constants
fuel_heat_value = 32000  # kJ/kg
specific_heat = 1.0      # kJ/kg·°C
heat_loss_coeff = 0.001  # proportional heat loss factor
ambient_temp = 30        # °C
co2_per_kg_fuel = 3.17   # kg CO2/kg coal

# Kiln physical parameters
kiln_radius = 3.0        # meters
kiln_length = 40.0       # meters
kiln_volume = np.pi * kiln_radius**2 * kiln_length  # m^3
kiln_mass = kiln_volume * 1200  # Assume clinker density = 1200 kg/m^3

# Streamlit UI
st.title("Cement Kiln Simulation with 3D Visualization")
st.sidebar.header("Input Parameters")

# Sidebar inputs
fuel_rate = st.sidebar.slider("Fuel Rate (kg/hr)", 100, 1000, 500)
motor_speed = st.sidebar.slider("Motor Speed (RPM)", 0.5, 5.0, 2.5, 0.1)
feed_rate = st.sidebar.slider("Feed Rate (kg/hr)", 500, 3000, 1200, 100)
temp_setpoint = st.sidebar.slider("Temperature Setpoint (°C)", 1000, 1500, 1350, 10)

# Derived values
residence_time = 30 / motor_speed
efficiency_factor = min(1.0, residence_time / 30)

# PID controller
def pid_control(error, integral, derivative):
    return Kp * error + Ki * integral + Kd * derivative

# Temperature differential equation
def kiln_model(T, t, fuel_rate, feed_rate):
    error = temp_setpoint - T
    integral = 0
    derivative = 0
    control_signal = pid_control(error, integral, derivative)
    
    fuel_rate_adjusted = max(100, min(1000, fuel_rate + control_signal))
    heat_input_kjs = fuel_rate_adjusted * fuel_heat_value / 3600
    effective_heat_input = heat_input_kjs * efficiency_factor

    heat_loss = heat_loss_coeff * (T - ambient_temp)
    dTdt = (effective_heat_input - heat_loss) / (kiln_mass * specific_heat)
    
    return dTdt

# Time points for simulation (e.g., 1 hour)
time = np.linspace(0, 3600, 1000)  # simulate for 1 hour (3600 seconds)
initial_temp = 400  # Starting temperature of the kiln

# Solve the differential equation
temperature = odeint(kiln_model, initial_temp, time, args=(fuel_rate, feed_rate))

# Final temperature after simulation
final_temp = temperature[-1]

# PID control simulation for temperature regulation
if final_temp >= 1350:
    quality = "✅ Good Clinker Formation"
elif final_temp >= 1200:
    quality = "⚠️ Partial Sintering"
else:
    quality = "❌ Poor Quality"

# CO2 emissions estimation
co2_emitted = fuel_rate * co2_per_kg_fuel  # kg/hr

# 3D Kiln Visualization
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Create the rotary kiln
theta = np.linspace(0, 2 * np.pi, 100)
z = np.linspace(0, kiln_length, 100)
X = kiln_radius * np.cos(theta)
Y = kiln_radius * np.sin(theta)

# Plot the kiln body
ax.plot_surface(X, Y, z[:, None], color='gray', edgecolor='black', alpha=0.7)

# Fuel simulation: Representing fuel flow into the kiln with color gradient
fuel_color_map = mcolors.LinearSegmentedColormap.from_list('fuel_colormap', ['orange', 'yellow', 'red'])
fuel = ax.scatter(X, Y, z, c=z, cmap=fuel_color_map, s=20)

# Adding fire effect: a simple flame effect at the outlet
fire_height = 2  # The height at which fire is simulated
fire = ax.scatter(0, 0, fire_height, c='red', s=100, alpha=0.8, marker='o')

# Set plot limits and labels
ax.set_xlim([-kiln_radius - 2, kiln_radius + 2])
ax.set_ylim([-kiln_radius - 2, kiln_radius + 2])
ax.set_zlim([0, kiln_length])
ax.set_xlabel('X-axis (meters)')
ax.set_ylabel('Y-axis (meters)')
ax.set_zlabel('Kiln Length (meters)')
ax.set_title('3D Cement Rotary Kiln Simulation')

# Function to update the animation (spinning kiln and fuel)
def update(frame):
    # Rotate the feed material to simulate kiln rotation
    angle = np.radians(frame)
    X_rot = kiln_radius * np.cos(theta + angle)
    Y_rot = kiln_radius * np.sin(theta + angle)
    
    # Update the kiln surface and fire effect position
    ax.cla()  # Clear previous frame
    ax.plot_surface(X_rot, Y_rot, z[:, None], color='gray', edgecolor='black', alpha=0.7)
    ax.scatter(X_rot, Y_rot, z, c=z, cmap=fuel_color_map, s=20)
    ax.scatter(0, 0, fire_height, c='red', s=100, alpha=0.8, marker='o')
    
    # Fire simulation (animate the flame movement)
    ax.scatter(0, 0, fire_height + np.sin(np.radians(frame)) * 0.2, c='orange', s=150, alpha=0.6, marker='o')

# Create the animation
ani = FuncAnimation(fig, update, frames=np.arange(0, 360, 5), interval=100, blit=False)

# Display the animation in Streamlit
st.pyplot(fig)

# Results and efficiency estimate
st.subheader("Results")
st.write(f"**Final Temperature:** {final_temp:.2f} °C")
st.write(f"**Estimated Product Quality:** {quality}")
st.write(f"**CO2 Emissions:** {co2_emitted:.2f} kg/hr")

# Savings Estimate (Example)
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
