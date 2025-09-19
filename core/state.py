import ctypes
from typing import assert_never, Optional
from core.conf import NUM_PLAYERS
from core.util import Vec2

PlayerId = ctypes.c_uint32

class Team:
    Self = 0
    Other = 1

Team_t = ctypes.c_uint8

class Score(ctypes.Structure):
    _fields_ = [
        ("self",  ctypes.c_uint32),
        ("other", ctypes.c_uint32),
    ]


class PlayerState(ctypes.Structure):
    _fields_ = [
        ("id", PlayerId),
        ("pos", Vec2),
        ("dir", Vec2),
        ("speed", ctypes.c_float),
        ("radius", ctypes.c_float),
        ("pickup_radius", ctypes.c_float),
    ]

class PlayerAction(ctypes.Structure):
    _fields_ = [
        ("dir", Vec2),
        ("has_pass", ctypes.c_bool),
        ("ball_pass", Vec2),
    ]

    def __init__(self, dir: Vec2, ball_pass: Optional[Vec2]):
        super().__init__()
        self.dir = dir
        if ball_pass is not None:
            self.has_pass = ctypes.c_bool(True)
            self.ball_pass = ball_pass
        else:
            self.has_pass = ctypes.c_bool(False)

class BallPossessionType:
    Possessed = 0
    Passing = 1
    Free = 2

class BallPossessed(ctypes.Structure):
    _fields_ = [
        ("owner", PlayerId),
        ("team", Team_t),
        ("capture_ticks", ctypes.c_uint32),
    ]

class BallPassing(ctypes.Structure):
    _fields_ = [
        ("team", Team_t),
    ]
class BallFree:
    pass

class _BallPossessionUnion(ctypes.Union):
    _fields_ = [
        ("possessed", BallPossessed),
        ("passing", BallPassing),
        # Free state has no data
    ]

class BallPossessionState(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint8),
        ("data", _BallPossessionUnion)
    ]

class BallStagnationState(ctypes.Structure):
    _fields_ = [
        ("center", Vec2),
        ("tick", ctypes.c_uint32),
    ]

class BallState(ctypes.Structure):
    _fields_ = [
        ("pos", Vec2),
        ("vel", Vec2),
        ("radius", ctypes.c_float),
    ]

class GameState(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint32),
        ("ball", BallState),
        ("_ball_possession", BallPossessionState),
        ("ball_stagnation", BallStagnationState),
        ("players", PlayerState * (2 * NUM_PLAYERS)),
        ("score", Score),
    ]

    @property
    def ball_possession(self):
        match self._ball_possession.type:
            case BallPossessionType.Possessed:
                return self._ball_possession.possessed
            case BallPossessionType.Passing:
                return self._ball_possession.passing
            case BallPossessionType.Free:
                return BallFree()
            case _ as unreachable:
                assert_never(unreachable)

    @property
    def is_ball_free(self):
        return self._ball_possession.type == BallPossessionType.Free

    @property
    def ball_owner(self):
        if self._ball_possession.type == BallPossessionType.Possessed:
            return self._ball_possession.data.possessed.owner
        return None

    def team_of(self, id: PlayerId):
        if id < NUM_PLAYERS:
            return Team.Self
        elif id < NUM_PLAYERS * 2:
            return Team.Other
        return None

    @property
    def teams(self):
        return (self.players[:NUM_PLAYERS], self.players[NUM_PLAYERS:])

    def team(self, team: Team) -> ctypes.Array[PlayerState]:
        if team == Team.Self:
            return self.players[:NUM_PLAYERS]
        else:
            return self.players[NUM_PLAYERS:]

