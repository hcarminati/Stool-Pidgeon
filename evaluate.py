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

    while game.state.phase != GamePhase.GAME_OVER and turns < MAX_TURNS:
        turns += 1
        if game.state.is_agent_turn():
            action = game.agent.choose_action()
            action.execute_action(game, GamePhase, agent=True)
        else:
            action = opponent.choose_action()
            action.execute_action(game, GamePhase)

    sys.stdout = sys.__stdout__

    # EV error only meaningful for agents that maintain a belief state
    if hasattr(game.agent, 'belief'):
        predicted_ev = game.agent.belief.expected_hand_value(1)
        actual_score = sum(c.value for c in game.agent_hands if c is not None and c.value is not None)
        ev_error = predicted_ev - actual_score
    else:
        ev_error = None

    return game.get_scores(), ev_error


def run_evaluation(label, agent_class, opponent_class=RandomAgent, n=NUM_GAMES):
    wins = {"agent": 0, "user": 0, "tie": 0}
    ev_errors = []

    print(f"\n=== {label} — starting {n} games ===", flush=True)
    with Pool(processes=10) as pool:
        results = []
        for i, result in enumerate(pool.starmap(play_game, [(agent_class, opponent_class)] * n), 1):
            results.append(result)
            if i % 10 == 0:
                print(f"  {i}/{n} done...", flush=True)

    for result, ev_err in results:
        wins[result["winner"]] += 1
        if ev_err is not None:
            ev_errors.append(ev_err)

    print(f"\n=== {label} ({n} games) ===")
    print(f"  Agent wins:    {wins['agent']}/{n} ({100*wins['agent']/n:.1f}%)")
    print(f"  Opponent wins: {wins['user']}/{n}  ({100*wins['user']/n:.1f}%)")
    print(f"  Ties:          {wins['tie']}/{n}")
    if ev_errors:
        print(f"  EV mean error: {np.mean(ev_errors):.2f}")
        print(f"  EV std error:  {np.std(ev_errors):.2f}")
        print(f"  EV MAE:        {np.mean(np.abs(ev_errors)):.2f}")
    else:
        print(f"  EV error:      N/A (no belief state)")


if __name__ == '__main__':
    run_evaluation("Heuristic vs Random",  HeuristicAgent,  RandomAgent,     n=NUM_GAMES)
    run_evaluation("POMDP vs Random",      BasicPOMDPAgent, RandomAgent,     n=NUM_GAMES)
    run_evaluation("POMDP vs Heuristic",   BasicPOMDPAgent, HeuristicAgent,  n=NUM_GAMES)
    run_evaluation("MC+POMDP vs Random",   MCPOMDPAgent,    RandomAgent,     n=NUM_GAMES)
    run_evaluation("MC+POMDP vs Heuristic", MCPOMDPAgent,    HeuristicAgent,  n=NUM_GAMES)
    run_evaluation("MC+POMDP vs POMDP",    MCPOMDPAgent,    BasicPOMDPAgent, n=NUM_GAMES)