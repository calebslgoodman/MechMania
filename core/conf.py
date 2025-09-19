import ctypes
from core.util import Vec2

NUM_PLAYERS = 4

class BallConfig(ctypes.Structure):
    _fields_ = [
        ("friction", ctypes.c_float),
        ("radius", ctypes.c_float),
        ("capture_ticks", ctypes.c_uint32),
        ("stagnation_radius", ctypes.c_float),
        ("stagnation_ticks", ctypes.c_uint32),
    ]

class PlayerConfig(ctypes.Structure):
    _fields_ = [
        ("radius", ctypes.c_float),
        ("pickup_radius", ctypes.c_float),
        ("speed", ctypes.c_float),
        ("pass_speed", ctypes.c_float),
        ("pass_error", ctypes.c_float),
        ("possession_slowdown", ctypes.c_float),
    ]

class FieldConfig(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
    ]

    def center(self) -> Vec2:
        return Vec2(self.width * 0.5, self.height * 0.5)

    def bottom_right(self) -> Vec2:
        return Vec2(self.width, self.height)

    def goal_a(self) -> Vec2:
        return Vec2(0.0, self.height * 0.5)

    def goal_b(self) -> Vec2:
        return Vec2(self.width, self.height * 0.5)


class GoalConfig(ctypes.Structure):
    _fields_ = [
        ("normal_height", ctypes.c_uint32),
        ("thickness", ctypes.c_uint32),
        ("penalty_box_width", ctypes.c_uint32),
        ("penalty_box_height", ctypes.c_uint32),
        ("penalty_box_radius", ctypes.c_uint32),
    ]

    def current_height(self, conf: "GameConfig", tick: int):
        if tick <= conf.max_ticks:
            return self.normal_height
        else:
            return conf.field.height

class GameConfig(ctypes.Structure):
    _fields_ = [
        ("max_ticks", ctypes.c_uint32),
        ("endgame_ticks", ctypes.c_uint32),
        ("spawn_ball_dist", ctypes.c_float),
        ("ball", BallConfig),
        ("player", PlayerConfig),
        ("field", FieldConfig),
        ("goal", GoalConfig),
    ]
