from StoolPigeonGame import StoolPigeonGame
from agents.basic_pomdp_agent.basic_pomdp_agent import BasicPOMDPAgent
from agents.monte_carlo_agent.mc_pomdp_agent import MCPOMDPAgent
from agents.heuristic_agent import HeuristicAgent
from agents.random_agent import RandomAgent
from game_state import GamePhase
import os, sys
import numpy as np
from multiprocessing import Pool

NUM_GAMES = 500
MAX_TURNS = 500

def play_game(agent_class, opponent_class=RandomAgent):
    sys.stdout = open(os.devnull, 'w')
    game = StoolPigeonGame(GUI=False, agent_class=agent_class)
    game.state.set_phase(GamePhase.DRAW)
    opponent = opponent_class(game, player_idx=0)
    turns = 0
    agent_knocked = False

    while game.state.phase != GamePhase.GAME_OVER and turns < MAX_TURNS:
        turns += 1

        # Track if the agent knocked
        if game.state.knocked_by == 1:
            agent_knocked = True

        if game.state.is_agent_turn():
            action = game.agent.choose_action()
            action.execute_action(game, GamePhase, agent=True)
        else:
            action = opponent.choose_action()
            action.execute_action(game, GamePhase)

    sys.stdout = sys.__stdout__

    scores = game.get_scores()

    # EV error: only meaningful for agents with a belief state
    if hasattr(game.agent, 'belief'):
        predicted_ev = game.agent.belief.expected_hand_value(1)
        actual_score = sum(c.value for c in game.agent_hands if c is not None and c.value is not None)
        ev_error = predicted_ev - actual_score
    else:
        ev_error = None

    # Knock accuracy: did the agent knock, and if so, did it win?
    knock_win = None
    if agent_knocked:
        knock_win = 1 if scores["winner"] == "agent" else 0

    return scores, ev_error, turns, knock_win


def run_evaluation(label, agent_class, opponent_class=RandomAgent, n=NUM_GAMES):
    wins = {"agent": 0, "user": 0, "tie": 0}
    ev_errors = []
    game_lengths = []
    agent_scores = []
    opponent_scores = []
    knock_wins = []

    print(f"\n=== {label} — starting {n} games ===", flush=True)
    with Pool(processes=10) as pool:
        results = []
        for i, result in enumerate(pool.starmap(play_game, [(agent_class, opponent_class)] * n), 1):
            results.append(result)
            if i % 10 == 0:
                print(f"  {i}/{n} done...", flush=True)

    for scores, ev_err, turns, knock_win in results:
        wins[scores["winner"]] += 1
        game_lengths.append(turns)
        agent_scores.append(scores["agent"])
        opponent_scores.append(scores["user"])
        if ev_err is not None:
            ev_errors.append(ev_err)
        if knock_win is not None:
            knock_wins.append(knock_win)

    print(f"\n=== {label} ({n} games) ===")
    print(f"  Agent wins:       {wins['agent']}/{n} ({100*wins['agent']/n:.1f}%)")
    print(f"  Opponent wins:    {wins['user']}/{n}  ({100*wins['user']/n:.1f}%)")
    print(f"  Ties:             {wins['tie']}/{n}")
    print(f"  Avg game length:  {np.mean(game_lengths):.1f} turns")
    print(f"  Avg agent score:  {np.mean(agent_scores):.2f}")
    print(f"  Avg opp score:    {np.mean(opponent_scores):.2f}")
    if knock_wins:
        print(f"  Knock accuracy:   {100*np.mean(knock_wins):.1f}% (agent knocked {len(knock_wins)} times)")
    if ev_errors:
        print(f"  EV mean error:    {np.mean(ev_errors):.2f}")
        print(f"  EV std error:     {np.std(ev_errors):.2f}")
        print(f"  EV MAE:           {np.mean(np.abs(ev_errors)):.2f}")
    else:
        print(f"  EV error:         N/A (no belief state)")


if __name__ == '__main__':
    run_evaluation("Heuristic vs Random",   HeuristicAgent,  RandomAgent,     n=NUM_GAMES)
    run_evaluation("POMDP vs Random",       BasicPOMDPAgent, RandomAgent,     n=NUM_GAMES)
    run_evaluation("POMDP vs Heuristic",    BasicPOMDPAgent, HeuristicAgent,  n=NUM_GAMES)
    run_evaluation("MC+POMDP vs Random",    MCPOMDPAgent,    RandomAgent,     n=NUM_GAMES)
    run_evaluation("MC+POMDP vs Heuristic", MCPOMDPAgent,    HeuristicAgent,  n=NUM_GAMES)
    run_evaluation("MC+POMDP vs POMDP",     MCPOMDPAgent,    BasicPOMDPAgent, n=NUM_GAMES)
