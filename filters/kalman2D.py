import numpy as np

class Kalman2D:
    def __init__(self, dt=1/30, process_var=1e-2, meas_var=5.0):
        self.dt = dt

        # State [x, y, vx, vy]
        self.x = np.zeros((4, 1))

        # State transition matrix
        self.F = np.array([[1, 0, dt, 0],
                           [0, 1, 0, dt],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]])

        # Measurement matrix
        self.H = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0]])

        # Covariances
        self.P = np.eye(4) * 500.0           # initial uncertainty
        self.Q = np.eye(4) * process_var     # process noise
        self.R = np.eye(2) * meas_var        # measurement noise

    def predict(self):
        # Predict next state
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(self.F, np.dot(self.P, self.F.T)) + self.Q
        return self.x[:2].flatten()  # return [x, y]

    def update(self, z):
        z = np.reshape(z, (2, 1))  # ensure column vector

        # Innovation / residual
        y = z - np.dot(self.H, self.x)

        # Innovation covariance
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R

        # Kalman gain
        K = np.dot(self.P, np.dot(self.H.T, np.linalg.inv(S)))

        # Update state estimate
        self.x = self.x + np.dot(K, y)

        # Update covariance
        I = np.eye(self.P.shape[0])
        self.P = (I - np.dot(K, self.H)) @ self.P

        return self.x[:2].flatten()
