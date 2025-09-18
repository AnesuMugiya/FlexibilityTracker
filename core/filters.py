"""
Handles MediaPipe pose landmark stabilization
"""

import math
class OneEuro:
    def __init__(self, freq, min_cutoff=1.0, beta=0.005, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = None

    def _alpha(self, cutoff):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / self.freq
        return 1.0 / (1.0 + tau/te)

    def __call__(self, x):
        # derivative
        dx = 0.0 if self.x_prev is None else (x - self.x_prev) * self.freq
        ad = self._alpha(self.d_cutoff)
        dx_hat = dx if self.dx_prev is None else ad*dx + (1-ad)*self.dx_prev
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff)
        x_hat = x if self.x_prev is None else a*x + (1-a)*self.x_prev
        self.x_prev, self.dx_prev = x_hat, dx_hat
        return x_hat
