from . import *
#mm-cli run
def get_strategy(team: int):
    """This function tells the engine what strategy you want your bot to use"""
    
    # team == 0 means I am on the left
    # team == 1 means I am on the right
    
    if team == 0:
        print("Hello! I am team A (on the left)")
        return Strategy(goalee_formation, strat1)
    else:
        print("Hello! I am team B (on the right)")
        return Strategy(goalee_formation, strat1)
    
    # NOTE when actually submitting your bot, you probably want to have the SAME strategy for both
    # sides.

def goalee_formation(score: Score) -> List[Vec2]:
    """The engine will call this function every time the field is reset:
    either after a goal, if the ball has not moved for too long, or right before endgame"""
    
    config = get_config()
    field = config.field.bottom_right()
    
    return [
        Vec2(field.x * 0.1, field.y * 0.5),
        Vec2(field.x * 0.4, field.y * 0.4),
        Vec2(field.x * 0.4, field.y * 0.5),
        Vec2(field.x * 0.4, field.y * 0.6),
    ]

def ball_chase(game: GameState) -> List[PlayerAction]:
    """Very simple strategy to chase the ball and shoot on goal"""
    
    config = get_config()
    
    # NOTE Do not worry about what side your bot is on! 
    # The engine mirrors the world for you if you are on the right, 
    # so to you, you always appear on the left.
    
    return [
        PlayerAction(
            game.ball.pos - game.players[i].pos,
            config.field.goal_other() - game.players[i].pos
        ) 
        for i in range(NUM_PLAYERS)
    ]


def strat1(game: GameState) -> List[PlayerAction]:
    """Very simple strategy to chase the ball and shoot on goal"""
    
    config = get_config()
    
    # NOTE Do not worry about what side your bot is on! 
    # The engine mirrors the world for you if you are on the right, 
    # so to you, you always appear on the left.
    # --- Capture game-level state ---
    tick = game.tick

    # Ball state
    ball_pos = game.ball.pos
    ball_vel = game.ball.vel
    ball_radius = game.ball.radius

    # Ball possession / metadata
    # Avoid calling `game.ball_possession` directly — that property can
    # raise an AttributeError in a ctypes/union edge case. Read the
    # low-level `_ball_possession` fields as a safe fallback.
    try:
        ball_possession = game.ball_possession
    except AttributeError:
        # Fallback: inspect the raw union/type
        t = int(getattr(game._ball_possession, "type", -1))
        if t == 0:
            # possessed
            ball_possession = game._ball_possession.data.possessed
        elif t == 1:
            # passing
            ball_possession = game._ball_possession.data.passing
        else:
            # free or unknown
            ball_possession = None

    # low-level possession type (ctypes field)
    ball_possession_type = int(getattr(game._ball_possession, "type", -1))

    # ball_owner: prefer the safe property, but guard against AttributeError
    try:
        ball_owner = game.ball_owner
    except AttributeError:
        ball_owner = None
        if ball_possession is not None and hasattr(ball_possession, "owner"):
            ball_owner = int(ball_possession.owner)

    # Ball stagnation
    ball_stagnation_center = game.ball_stagnation.center
    ball_stagnation_tick = game.ball_stagnation.tick

    # Players and teams
    players = game.players
    teams = game.teams
    self_team_players = game.team(Team.Self)
    other_team_players = game.team(Team.Other)

    # Score
    score_self = game.score.self
    score_other = game.score.other

    # --- Capture config-level values ---
    cfg = config
    max_ticks = cfg.max_ticks
    endgame_ticks = cfg.endgame_ticks
    spawn_ball_dist = cfg.spawn_ball_dist

    # Field and goal
    field = cfg.field
    field_width = field.width
    field_height = field.height
    field_center = field.center()
    field_bottom_right = field.bottom_right()
    goal_self = field.goal_self()
    goal_other = field.goal_other()

    # Player configuration
    player_cfg = cfg.player
    player_radius = player_cfg.radius
    player_pickup_radius = player_cfg.pickup_radius
    player_speed = player_cfg.speed
    player_pass_speed = player_cfg.pass_speed
    player_pass_error = player_cfg.pass_error
    player_possession_slowdown = player_cfg.possession_slowdown

    # Ball configuration
    ball_cfg = cfg.ball
    ball_friction = ball_cfg.friction
    ball_capture_ticks = ball_cfg.capture_ticks
    ball_stagnation_radius = ball_cfg.stagnation_radius
    ball_stagnation_ticks = ball_cfg.stagnation_ticks

    # Goal configuration
    goal_cfg = cfg.goal
    goal_normal_height = goal_cfg.normal_height
    goal_thickness = goal_cfg.thickness
    goal_penalty_box_width = goal_cfg.penalty_box_width
    goal_penalty_box_height = goal_cfg.penalty_box_height
    goal_penalty_box_radius = goal_cfg.penalty_box_radius

    # Constants
    num_players = NUM_PLAYERS
    # --- Build team player lists as requested ---
    our_team = [
        {"position": p.pos, "direction": p.dir, "speed": p.speed}
        for p in self_team_players
    ]

    other_team = [
        {"position": p.pos, "direction": p.dir, "speed": p.speed}
        for p in other_team_players
    ]

    # Ball position and speed
    ball_position = ball_pos
    # use Vec2.norm() helper to compute scalar speed
    ball_speed = ball_vel.norm()

    # Ball possession boolean (True if some player currently possesses the ball)
    ball_possessed = (ball_owner is not None)

    # ball_team: None, or "us" / "them"
    if ball_owner is None:
        ball_team = None
    else:
        ball_team = "us" if game.team_of(ball_owner) == Team.Self else "them"

    # ball_player: None, or index 0..(NUM_PLAYERS-1) within owning team
    if ball_owner is None:
        ball_player = None
    else:
        # convert global player id into per-team index
        if ball_owner < NUM_PLAYERS:
            ball_player = int(ball_owner)
        else:
            ball_player = int(ball_owner - NUM_PLAYERS)


    print(our_team[0]["position"].x)


    return [
        PlayerAction(
            game.ball.pos - game.players[i].pos,
            config.field.goal_other() - game.players[i].pos
        ) 
        for i in range(NUM_PLAYERS)
    ]

    #mm-cli run



def do_nothing(game: GameState) -> List[PlayerAction]:
    """This strategy will do nothing :("""
    
    return [
        PlayerAction(Vec2(0, 0), None) 
        for _ in range(NUM_PLAYERS)
    ]
