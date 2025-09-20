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
        return Strategy(goalee_formation, ball_chase)
    
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


    # --- Strategy implementation (use only the variables we created) ---
    # debug flag: set True to enable writing pass/shot events to a unique file under debug_files
    should_debug = True

    # safe debug logger: creates a unique file on the first tick (does not overwrite existing files)
    # and only appends when an event occurs (pass/shot).
    def log_debug_event(event_type: str, player_idx: int, target: Vec2):
        if not should_debug:
            return
        try:
            from pathlib import Path
            from datetime import datetime
            debug_dir = Path(__file__).resolve().parents[0].joinpath('debug_files')
            debug_dir.mkdir(parents=True, exist_ok=True)

            # on first use, create a unique file and store path on the function object
            if not getattr(strat1, 'debug_inited', False):
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_name = f'mm_debug_{ts}.txt'
                fpath = debug_dir.joinpath(base_name)
                counter = 1
                while fpath.exists():
                    fpath = debug_dir.joinpath(f'mm_debug_{ts}_{counter}.txt')
                    counter += 1
                # create and write header
                with fpath.open('w', encoding='utf-8') as fh:
                    fh.write('tick\tevent\tplayer\ttarget\n')
                strat1.debug_file = fpath
                strat1.debug_inited = True

            fpath = getattr(strat1, 'debug_file', None)
            if fpath is None:
                return
            # append the event line
            with fpath.open('a', encoding='utf-8') as fh:
                fh.write(f"{int(tick)}\t{event_type}\tplayer={player_idx}\ttarget=({target.x:.3f},{target.y:.3f})\n")
        except Exception:
            # never crash the strategy for logging errors
            pass
    # helpers
    def to_norm(v: Vec2) -> Vec2:
        # normalized coordinates where (1,1) == field dimensions
        return Vec2(v.x / field_width, v.y / field_height)

    def dist_norm(a: Vec2, b: Vec2) -> float:
        na = to_norm(a); nb = to_norm(b)
        return (na - nb).norm()

    def point_line_dist_norm(p: Vec2, a: Vec2, b: Vec2) -> float:
        # compute distance from point p to line through a->b in normalized space
        na = to_norm(a); nb = to_norm(b); np = to_norm(p)
        ab = nb - na
        denom = ab.dot(ab)
        if denom == 0:
            return (np - na).norm()
        t = (np - na).dot(ab) / denom
        proj = Vec2(na.x + ab.x * t, na.y + ab.y * t)
        return (np - proj).norm()

    # initialize decisions for each of our team players (0..NUM_PLAYERS-1)
    decisions = [ {"go_position": our_team[i]["position"], "go_pass": None} for i in range(num_players) ]

    # Goalkeeper (player 0) — keep original starting x
    if not hasattr(strat1, "goalkeeper_x"):
        strat1.goalkeeper_x = our_team[0]["position"].x
    gkx = strat1.goalkeeper_x
    goal_point = Vec2(0.0 * field_width, 0.5 * field_height)
    # line from ball to goal_point: ball_position + t*(goal_point - ball_position)
    bp = ball_position
    line_dx = (goal_point.x - bp.x)
    line_dy = (goal_point.y - bp.y)
    if line_dx == 0:
        # vertical line: place goalkeeper at midpoint y between ball and goal
        gy = (bp.y + goal_point.y) * 0.5
    else:
        t = (gkx - bp.x) / line_dx
        gy = bp.y + t * line_dy
    # clamp
    gy = max(0.0, min(field_height, gy))
    decisions[0]["go_position"] = Vec2(gkx, gy)

    # If goalkeeper has the ball, pass immediately (choose best of three directions)
    if ball_team == "us" and ball_player == 0:
        kp = our_team[0]["position"]
        # candidate directions: up-right (45deg), right, down-right (-45deg)
        cand_dirs = [Vec2(1.0, 1.0).normalize(), Vec2(1.0, 0.0).normalize(), Vec2(1.0, -1.0).normalize()]
        best_dir = None
        best_min_dist = -1.0
        # consider passes as a long segment from keeper position towards far point
        for d in cand_dirs:
            target = Vec2(kp.x + d.x * field_width * 0.5, kp.y + d.y * field_height * 0.5)
            # compute minimum distance from defenders to line kp->target
            min_dist = min((point_line_dist_norm(Vec2(def_p["position"].x, def_p["position"].y), kp, target) for def_p in other_team), default=1e9)
            if min_dist > best_min_dist:
                best_min_dist = min_dist
                best_dir = d
        pass_target = Vec2(kp.x + best_dir.x * field_width * 0.5, kp.y + best_dir.y * field_height * 0.5)
        decisions[0]["go_pass"] = pass_target
        # log keeper pass event
        try:
            log_debug_event("pass", 0, pass_target)
        except Exception:
            pass

    # Determine roles for the other players (indices 1..3)
    # prepare list of indices excluding goalkeeper
    role_indices = [i for i in range(1, num_players)]

    # helper: choose chaser index based on rules
    def choose_chaser(consider_leftness: bool) -> int:
        # candidates on or to the left of the ball (x <= ball.x)
        candidates = []
        for i in role_indices:
            p = our_team[i]["position"]
            if not consider_leftness or p.x <= ball_position.x:
                candidates.append((i, dist_norm(p, ball_position)))
        if candidates:
            # choose closest by distance
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]
        # fallback: left-most player
        leftmost = min(role_indices, key=lambda i: our_team[i]["position"].x)
        return leftmost

    if ball_team == "them":
        chaser_idx = choose_chaser(consider_leftness=True)
    elif ball_team is None or not ball_possessed:
        chaser_idx = choose_chaser(consider_leftness=False)
    else:
        # we have the ball: chaser is ball holder
        chaser_idx = ball_player if ball_player is not None else choose_chaser(False)

    # Assign chaser to head straight for the ball (or goal if attacker)
    if ball_team == "us" and ball_player is not None:
        # attacking: player with the ball runs towards goal
        attacker_idx = ball_player
        attacker_pos = our_team[attacker_idx]["position"]
        goal_center = Vec2(1.0 * field_width, 0.5 * field_height)
        decisions[attacker_idx]["go_position"] = goal_center

        # other supporting players (exclude goalkeeper and attacker)
        supporters = [i for i in range(num_players) if i not in (0, attacker_idx)]
        # front x: 0.1 in front of attacking player (towards goal)
        front_x = attacker_pos.x + 0.1 * field_width
        front_x = max(0.0, min(field_width, front_x))
        # assign above/below by current y ordering
        s0, s1 = supporters[0], supporters[1]
        p0y = our_team[s0]["position"].y; p1y = our_team[s1]["position"].y
        if p0y > p1y:
            # s0 is higher -> assign top
            decisions[s0]["go_position"] = Vec2(front_x, attacker_pos.y + 0.3 * field_height)
            decisions[s1]["go_position"] = Vec2(front_x, attacker_pos.y - 0.3 * field_height)
        else:
            decisions[s0]["go_position"] = Vec2(front_x, attacker_pos.y - 0.3 * field_height)
            decisions[s1]["go_position"] = Vec2(front_x, attacker_pos.y + 0.3 * field_height)

        # passing/shooting logic for attacker
        # compute defender positions
        defenders = [Vec2(d["position"].x, d["position"].y) for d in other_team]

        # if any defender is within 0.15 (normalized) of attacker, consider passing
        # (use defenders, not supporters)
        defender_close = any(dist_norm(def_p, attacker_pos) <= 0.15 for def_p in defenders)

        def best_pass_target(from_pos: Vec2, targets: list[Vec2]) -> Vec2:
            # choose target whose passing line has max minimum distance to any defender
            best_t = None; best_score = -1.0
            for tgt in targets:
                min_d = min((point_line_dist_norm(def_p, from_pos, tgt) for def_p in defenders), default=1e9)
                if min_d > best_score:
                    best_score = min_d; best_t = tgt
            return best_t, best_score

        # check shooting condition: attacker within 0.25 of goal center
        if dist_norm(attacker_pos, Vec2(field_width, 0.5 * field_height)) <= 0.25:
            shot_targets = [Vec2(field_width, 0.55 * field_height), Vec2(field_width, 0.5 * field_height), Vec2(field_width, 0.45 * field_height)]
            best_shot, best_shot_score = best_pass_target(attacker_pos, shot_targets)
            if best_shot_score >= 0.05:
                # shoot to the best_shot
                decisions[attacker_idx]["go_pass"] = best_shot
                try:
                    log_debug_event("shot", attacker_idx, best_shot)
                except Exception:
                    pass
            else:
                # fallback to passing to supporters
                pass_targets = [our_team[s]["position"] for s in supporters]
                best_tgt, _ = best_pass_target(attacker_pos, pass_targets)
                decisions[attacker_idx]["go_pass"] = best_tgt
                try:
                    log_debug_event("pass", attacker_idx, best_tgt)
                except Exception:
                    pass
        elif defender_close:
            # consider passing to best of supporters
            pass_targets = [our_team[s]["position"] for s in supporters]
            best_tgt, _ = best_pass_target(attacker_pos, pass_targets)
            decisions[attacker_idx]["go_pass"] = best_tgt
            try:
                log_debug_event("pass", attacker_idx, best_tgt)
            except Exception:
                pass

    else:
        # defensive / neutral modes: assign chaser and two positional players
        chaser_pos = our_team[chaser_idx]["position"]
        decisions[chaser_idx]["go_position"] = ball_position

        # remaining supporters (exclude goalkeeper and chaser)
        supporters = [i for i in range(num_players) if i not in (0, chaser_idx)]
        # assign positions at same x as ball, offset by 0.3 normalized in y
        top_y = ball_position.y + 0.3 * field_height
        bot_y = ball_position.y - 0.3 * field_height
        # ensure within bounds
        top_y = max(0.0, min(field_height, top_y))
        bot_y = max(0.0, min(field_height, bot_y))
        # decide who goes top/bottom by current y
        s0, s1 = supporters[0], supporters[1]
        p0y = our_team[s0]["position"].y; p1y = our_team[s1]["position"].y
        if p0y > p1y:
            decisions[s0]["go_position"] = Vec2(ball_position.x, top_y)
            decisions[s1]["go_position"] = Vec2(ball_position.x, bot_y)
        else:
            decisions[s0]["go_position"] = Vec2(ball_position.x, bot_y)
            decisions[s1]["go_position"] = Vec2(ball_position.x, top_y)

    # Build PlayerAction list from decisions
    actions = []
    for i in range(num_players):
        cur_pos = our_team[i]["position"]
        target = decisions[i]["go_position"]
        dir_vec = Vec2(target.x - cur_pos.x, target.y - cur_pos.y)
        pass_vec = decisions[i]["go_pass"] if decisions[i]["go_pass"] is not None else None
        actions.append(PlayerAction(dir_vec, pass_vec))

    return actions

    #mm-cli run



def do_nothing(game: GameState) -> List[PlayerAction]:
    """This strategy will do nothing :("""
    
    return [
        PlayerAction(Vec2(0, 0), None) 
        for _ in range(NUM_PLAYERS)
    ]
