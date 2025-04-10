import numpy as np
import pandas as pd

# -----------------------------
# EKF Drone Model Setup
# -----------------------------
# State vector: x = [p_x, p_y, p_z, v_x, v_y, v_z, phi, theta, psi, p, q, r]^T
#   - Position: p_x, p_y, p_z
#   - Velocity: v_x, v_y, v_z
#   - Euler angles (roll, pitch, yaw): phi, theta, psi
#   - Angular velocity: p, q, r
#
# Control input (IMU measurements): u = [a_x, a_y, a_z, omega_x, omega_y, omega_z]^T
#   - a: accelerometer (assumed to be in world frame for simplicity)
#   - omega: gyro measurements (used directly to update attitude)
#
# Process model:
#   p_new    = p + v*dt
#   v_new    = v + a*dt
#   e_new    = e + omega*dt      (e = Euler angles)
#   omega_new= omega              (assume constant angular velocity)
#
# Measurement model:
#   z = h(x) = [p_x, p_y, p_z]^T
#   (derived from the vision “poses” field; we use only the position part)
#

# ----- Process Model -----
def f(x, u, dt):
    """
    Process model for the drone.
    
    x: 12x1 state vector
    u: 6x1 control input [a_x, a_y, a_z, omega_x, omega_y, omega_z]^T
    dt: time step
    """
    p = x[0:3]       # position
    v = x[3:6]       # velocity
    e = x[6:9]       # Euler angles (roll, pitch, yaw)
    w = x[9:12]      # angular velocity
    
    a = u[0:3]       # simulated acceleration
    omega_meas = u[3:6]  # simulated gyro measurement
    
    p_new = p + v * dt
    v_new = v + a * dt
    e_new = e + omega_meas * dt   # update attitude
    w_new = w  # assume constant angular velocity
    
    return np.vstack((p_new, v_new, e_new, w_new))

def F_jacobian(dt):
    """
    Jacobian of the process model f with respect to state x.
    For our simple linear model, it is constant:
    
        [ I, dt*I,  0,    0 ]
        [ 0,   I,   0,    0 ]
        [ 0,   0,   I,    0 ]
        [ 0,   0,   0,    I ]
    """
    I3 = np.eye(3)
    F = np.block([
        [I3, dt * I3, np.zeros((3, 3)), np.zeros((3, 3))],
        [np.zeros((3, 3)), I3, np.zeros((3, 3)), np.zeros((3, 3))],
        [np.zeros((3, 3)), np.zeros((3, 3)), I3, np.zeros((3, 3))],
        [np.zeros((3, 3)), np.zeros((3, 3)), np.zeros((3, 3)), I3]
    ])
    return F

# ----- Measurement Model -----
def h(x):
    """
    Measurement model: return the position (first three elements).
    """
    return x[0:3]

def H_jacobian():
    """
    Jacobian of h with respect to x.
    h(x) = [p_x, p_y, p_z]^T, so H = [I, 0] with dimensions 3x12.
    """
    I3 = np.eye(3)
    H = np.hstack([I3, np.zeros((3, 9))])
    return H

# ----- Extended Kalman Filter Class -----
class ExtendedKalmanFilter:
    def __init__(self, state_dim, meas_dim):
        self.x = np.zeros((state_dim, 1))  # 12x1 state vector
        self.P = np.eye(state_dim)         # state covariance
        self.Q = np.eye(state_dim) * 0.05    # process noise covariance (tunable)
        self.R = np.eye(meas_dim) * 0.1      # measurement noise covariance (tunable)

    def predict(self, u, dt):
        self.x = f(self.x, u, dt)
        F = F_jacobian(dt)
        self.P = F @ self.P @ F.T + self.Q

    def update(self, z):
        z_pred = h(self.x)
        H = H_jacobian()
        y = z - z_pred                # innovation
        S = H @ self.P @ H.T + self.R   # innovation covariance
        K = self.P @ H.T @ np.linalg.inv(S)  # Kalman gain
        self.x = self.x + K @ y
        self.P = (np.eye(self.x.shape[0]) - K @ H) @ self.P

# ----- Pose Parsing Function -----
def parse_pose(pose_data):
    """
    Parse the 'poses' string into a 3x1 position measurement.
    Expects tuple format like "(x, y, z, ...)" and uses the first three values.
    """
    if not isinstance(pose_data, str):
        return np.zeros((3, 1))
    pose_data = pose_data.strip()
    if pose_data.startswith("(") and pose_data.endswith(")"):
        try:
            content = pose_data[1:-1]
            parts = [p.strip() for p in content.split(',')]
            pos = np.array([float(parts[i]) for i in range(3)]).reshape(-1, 1)
            return pos
        except Exception as e:
            print("Error parsing tuple pose:", e)
            return np.zeros((3, 1))
    try:
        parts = pose_data.replace('(', '').replace(')', '').split(',')
        if len(parts) < 3:
            parts = pose_data.split()
        pos = np.array([float(x) for x in parts[:3]]).reshape(-1, 1)
        return pos
    except Exception as e:
        print("Error parsing pose:", e)
        return np.zeros((3, 1))

# ----- Single EKF Step Function -----
    """
    Perform a single EKF step.
    
    Inputs:
      ekf            : An instance of ExtendedKalmanFilter (with current state & covariance).
      row            : A single row of CSV data (as a Pandas Series) containing at least the 'poses' field.
      dt             : Time difference between current and previous step.
      imu_measurement: A 6x1 numpy array representing the control input [a_x, a_y, a_z, omega_x, omega_y, omega_z].
    
    Process:
      1. Use imu_measurement and dt to predict the next state.
      2. Parse the 'poses' measurement from the row.
      3. Use the measurement to update the state.
    
    Returns:
      The updated state vector (12x1 numpy array).
    """
    
def ekf_step(ekf, row, dt, imu_measurement):
    # Predict step using provided IMU measurement
    ekf.predict(imu_measurement, dt)
    
    # Parse the vision-based pose measurement from the CSV row.
    z = parse_pose(row['poses'])
    
    # Update the EKF with the measurement.
    ekf.update(z)
    
    return ekf.x

