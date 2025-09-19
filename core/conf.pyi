import ctypes

class BallConfig(ctypes.Structure):
    friction: ctypes.c_float
    radius: ctypes.c_float
    capture_ticks: ctypes.c_uint32
    stagnation_radius: ctypes.c_float
    stagnation_ticks: ctypes.c_uint32

class PlayerConfig(ctypes.Structure):
    radius: ctypes.c_float
    pickup_radius: ctypes.c_float
    speed: ctypes.c_float
    pass_speed: ctypes.c_float
    pass_error: ctypes.c_float
    possession_slowdown: ctypes.c_float

class FieldConfig(ctypes.Structure):
    width: ctypes.c_uint32
    height: ctypes.c_uint32

class GoalConfig(ctypes.Structure):
    normal_height: ctypes.c_uint32
    thickness: ctypes.c_uint32
    penalty_box_width: ctypes.c_uint32
    penalty_box_height: ctypes.c_uint32
    penalty_box_radius: ctypes.c_uint32

class GameConfig(ctypes.Structure):
    max_ticks: ctypes.c_uint32
    endgame_ticks: ctypes.c_uint32
    spawn_ball_dist: ctypes.c_float
    ball: BallConfig
    player: PlayerConfig
    field: FieldConfig
    goal: GoalConfig
