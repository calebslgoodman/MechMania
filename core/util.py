import ctypes
import math

class Vec2(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]

    def __add__(self, other) -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other) -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar) -> "Vec2":
        return self.__mul__(scalar)

    def normalize(self) -> "Vec2":
        magnitude = math.sqrt(self.x**2 + self.y**2)
        if magnitude == 0:
            return Vec2(0, 0)
        return Vec2(self.x/magnitude, self.y/magnitude)

    def rotate(self, angle_deg: float) -> "Vec2":
        """Rotates the vector by a given angle in degrees."""
        angle_rad = math.radians(angle_deg) # Convert degrees to radians
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        new_x = self.x * cos_a - self.y * sin_a
        new_y = self.x * sin_a + self.y * cos_a
        return Vec2(new_x, new_y)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def norm_sq(self) -> float:
        return self.dot(self)

    def norm(self) -> float:
        return (self.dot(self))**0.5

    def theta(self) -> float:
        return math.atan2(self.y, self.x)

    def dist(self, other: "Vec2") -> float:
        return (self - other).norm()

    def dist_sq(self, other: "Vec2") -> float:
        return (self - other).norm_sq()
