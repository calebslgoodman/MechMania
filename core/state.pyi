import ctypes
from ctypes import Array
from typing import Union, Tuple, Optional
from core.util import Vec2

PlayerId = ctypes.c_uint32

class Team:
    Self: int
    Other: int

Team_t = ctypes.c_uint8

class Score(ctypes.Structure):
    self: ctypes.c_uint32
    other: ctypes.c_uint32


class PlayerState(ctypes.Structure):
    id: PlayerId
    pos: Vec2
    dir: Vec2
    speed: ctypes.c_float
    pickup_radius: ctypes.c_float

class PlayerAction(ctypes.Structure):
    dir: Vec2
    has_pass: ctypes.c_bool
    ball_pass: Vec2

    def __init__(self, dir: Vec2, ball_pass: Optional[Vec2]): ...

class BallPossessionType:
    Possessed: int
    Passing: int
    Free: int

class BallPossessed(ctypes.Structure):
    owner: PlayerId
    team: Team_t
    capture_ticks: ctypes.c_uint32

class BallPassing(ctypes.Structure):
    team: Team_t

class BallFree:
    pass

class _BallPossessionUnion(ctypes.Union):
    possessed: BallPossessed
    passing: BallPassing

class BallPossessionState(ctypes.Structure):
    type: ctypes.c_uint8
    data: _BallPossessionUnion

class BallStagnationState(ctypes.Structure):
    center: Vec2
    tick: ctypes.c_uint32
class BallState(ctypes.Structure):
    pos: Vec2
    vel: Vec2
    radius: ctypes.c_float

class GameState(ctypes.Structure):
    tick: ctypes.c_uint32
    ball: BallState
    _ball_possession: BallPossessionState
    ball_stagnation: BallStagnationState
    players: ctypes.Array[PlayerState]
    score: Score

    @property
    def ball_possession(self) -> Union[BallPossessed, BallPassing, BallFree]: ...
    @property
    def is_ball_free(self) -> bool: ...
    @property
    def ball_owner(self) -> None | PlayerId: ...

    def team_of(self, id: PlayerId) -> None | Team: ...
    def teams(self) -> Tuple[Array[PlayerState], Array[PlayerState]]: ...
    def team(self, team: Team) -> Array[PlayerState]: ...
