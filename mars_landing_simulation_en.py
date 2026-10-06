"""
Mars Landing Simulation - Suicide Burn Guidance

Simulates a controlled Mars landing using the "suicide burn" technique
used by real Mars/Moon landers: the vehicle free-falls as long as
possible, then ignites its engine at the latest safe moment to bring
velocity to (near) zero exactly at touchdown.
"""

import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Physical / control constants
# ----------------------------------------------------------------------
MARS_GRAVITY = 3.71          # Mars gravity (m/s^2)
MAX_ENGINE_DECEL = 7.4       # Max engine deceleration (m/s^2)
TIME_STEP = 0.01             # Simulation time step (s)
UPPER_THRESHOLD = -0.1       # Upper hysteresis threshold (engine off)
LOWER_THRESHOLD = -0.3       # Lower hysteresis threshold (engine on)
MIN_BURN_DURATION = 0.5      # Minimum engine on/off duration (s)
SAFETY_MARGIN = 1.05         # Ignition safety margin
FUEL_CONSUMPTION_RATE = 1.5  # Fuel consumption rate (kg/s)
MAX_SIM_TIME = 100.0         # Simulation safety timeout (s)


def simulate_landing(initial_altitude, initial_velocity, initial_fuel):
    """
    Runs the full descent simulation for given initial conditions.

    Parameters:
        initial_altitude : initial altitude (m)
        initial_velocity : initial velocity (m/s, negative = downward)
        initial_fuel     : initial fuel mass (kg)

    Returns:
        dict with time/altitude/velocity/engine/fuel history and summary
    """
    altitude = initial_altitude
    velocity = initial_velocity
    fuel = initial_fuel

    engine_has_ignited = False
    engine_on = False
    last_switch_time = -999.0

    time_hist, altitude_hist, velocity_hist, engine_hist, fuel_hist = [], [], [], [], []

    t = 0.0
    while altitude > 0 and t < MAX_SIM_TIME:
        time_hist.append(t)
        altitude_hist.append(altitude)
        velocity_hist.append(velocity)
        engine_hist.append(1 if engine_on else 0)
        fuel_hist.append(fuel)

        # Ignition decision: fire the engine at the last safe moment,
        # based on the net deceleration available and a safety margin.
        stopping_distance = SAFETY_MARGIN * velocity**2 / (2 * (MAX_ENGINE_DECEL - MARS_GRAVITY))
        if not engine_has_ignited and altitude <= stopping_distance and fuel > 0:
            engine_has_ignited = True
            engine_on = True
            last_switch_time = t

        # Hysteresis control with a minimum on/off duration, so the
        # engine cannot switch faster than a real valve/engine could.
        if engine_has_ignited:
            time_since_switch = t - last_switch_time
            if engine_on and velocity > UPPER_THRESHOLD and time_since_switch >= MIN_BURN_DURATION:
                engine_on = False
                last_switch_time = t
            elif (not engine_on) and velocity < LOWER_THRESHOLD and time_since_switch >= MIN_BURN_DURATION and fuel > 0:
                engine_on = True
                last_switch_time = t

        # Fuel consumption while the engine is on; force shutdown if empty.
        if engine_on:
            fuel -= FUEL_CONSUMPTION_RATE * TIME_STEP
            if fuel <= 0:
                fuel = 0
                engine_on = False

        # Physics update (semi-implicit Euler integration).
        acceleration = (-MARS_GRAVITY + MAX_ENGINE_DECEL) if engine_on else -MARS_GRAVITY
        velocity = velocity + acceleration * TIME_STEP
        altitude = altitude + velocity * TIME_STEP
        t = t + TIME_STEP

    return {
        "time": time_hist, "altitude": altitude_hist, "velocity": velocity_hist,
        "engine": engine_hist, "fuel": fuel_hist,
        "touchdown_velocity": velocity, "descent_duration": t, "remaining_fuel": fuel,
    }


# ----------------------------------------------------------------------
# 1) Reference scenario + full 4-panel plot
# ----------------------------------------------------------------------
reference = simulate_landing(initial_altitude=500.0, initial_velocity=-20.0, initial_fuel=40.0)
print(f"[Reference] Touchdown velocity: {reference['touchdown_velocity']:.2f} m/s | "
      f"Duration: {reference['descent_duration']:.2f} s | Remaining fuel: {reference['remaining_fuel']:.2f} kg")

fig, axs = plt.subplots(1, 4, figsize=(18, 4))
axs[0].plot(reference["time"], reference["altitude"])
axs[0].set_title("Altitude vs Time")
axs[0].set_xlabel("Time (s)"); axs[0].set_ylabel("Altitude (m)"); axs[0].grid(True)

axs[1].plot(reference["time"], reference["velocity"], color="red")
axs[1].set_title("Velocity vs Time")
axs[1].set_xlabel("Time (s)"); axs[1].set_ylabel("Velocity (m/s)"); axs[1].grid(True)

axs[2].plot(reference["time"], reference["engine"], color="green")
axs[2].set_title("Engine State")
axs[2].set_xlabel("Time (s)"); axs[2].set_ylabel("0 = off, 1 = on"); axs[2].grid(True)

axs[3].plot(reference["time"], reference["fuel"], color="orange")
axs[3].set_title("Fuel vs Time")
axs[3].set_xlabel("Time (s)"); axs[3].set_ylabel("Fuel (kg)"); axs[3].grid(True)

plt.tight_layout()
plt.show()

# ----------------------------------------------------------------------
# 2) Fuel stress test + threshold plot
# ----------------------------------------------------------------------
fuel_values = [5, 10, 15, 20, 25, 26, 27, 28, 29, 30, 35, 40, 45]
touchdown_velocities = []
for fv in fuel_values:
    r = simulate_landing(initial_altitude=500.0, initial_velocity=-20.0, initial_fuel=fv)
    touchdown_velocities.append(r["touchdown_velocity"])
    print(f"Fuel={fv} kg -> Touchdown velocity={r['touchdown_velocity']:.2f} m/s, "
          f"Remaining fuel={r['remaining_fuel']:.2f} kg")

plt.figure(figsize=(8, 5))
plt.plot(fuel_values, touchdown_velocities, marker="o", color="purple")
plt.axhline(y=-1.48, color="green", linestyle="--", label="Safe landing velocity (~-1.48 m/s)")
plt.axvline(x=28, color="red", linestyle="--", label="Critical fuel threshold (~28 kg)")
plt.xlabel("Initial Fuel (kg)"); plt.ylabel("Touchdown Velocity (m/s)")
plt.title("Effect of Fuel Amount on Landing Safety")
plt.legend(); plt.grid(True); plt.tight_layout()
plt.show()

# ----------------------------------------------------------------------
# 3) Scenario stress test + summary bar chart
# ----------------------------------------------------------------------
scenarios = [
    {"altitude": 300.0, "velocity": -10.0, "label": "Low altitude\nslow entry"},
    {"altitude": 300.0, "velocity": -30.0, "label": "Low altitude\nfast entry"},
    {"altitude": 500.0, "velocity": -20.0, "label": "Mid altitude\nreference"},
    {"altitude": 800.0, "velocity": -20.0, "label": "High altitude\nmid entry"},
    {"altitude": 800.0, "velocity": -40.0, "label": "High altitude\nfast entry"},
    {"altitude": 1000.0, "velocity": -50.0, "label": "Very high altitude\nvery fast entry"},
]

labels, scenario_velocities = [], []
for sc in scenarios:
    result = simulate_landing(initial_altitude=sc["altitude"], initial_velocity=sc["velocity"], initial_fuel=50.0)
    labels.append(sc["label"])
    scenario_velocities.append(result["touchdown_velocity"])
    print(f"{sc['label'].replace(chr(10), ' '):28s} -> Touchdown velocity={result['touchdown_velocity']:.2f} m/s, "
          f"Remaining fuel={result['remaining_fuel']:.2f} kg")

colors = ["green" if abs(v) < 2.0 else "red" for v in scenario_velocities]
plt.figure(figsize=(9, 5))
plt.bar(labels, scenario_velocities, color=colors)
plt.axhline(y=-2.0, color="gray", linestyle="--", label="Soft landing limit (~-2 m/s)")
plt.ylabel("Touchdown Velocity (m/s)")
plt.title("Landing Performance Across Scenarios")
plt.legend(); plt.grid(True, axis="y"); plt.tight_layout()
plt.show()
