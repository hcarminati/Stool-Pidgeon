from StoolPigeonGame import StoolPigeonGame
from agents.basic_pomdp_agent.basic_pomdp_agent import BasicPOMDPAgent
from agents.monte_carlo_agent.mc_pomdp_agent import MCPOMDPAgent
from agents.random_agent import RandomAgent
from game_state import GamePhase
import os, sys
import numpy as np

NUM_GAMES = 100 

def play_game(agent_class, opponent_class=RandomAgent):
    sys.stdout = open(os.devnull, 'w')
    game = StoolPigeonGame(GUI=False, agent_class=agent_class)
    game.state.set_phase(GamePhase.DRAW)
    opponent = opponent_class(game)

    while game.state.phase != GamePhase.GAME_OVER:
        if game.state.is_agent_turn():
            action = game.agent.choose_action()
            action.execute_action(game, GamePhase, agent=True)
        else:
            action = opponent.choose_action()
            action.execute_action(game, GamePhase)

    sys.stdout = sys.__stdout__
    predicted_ev = game.agent.belief.expected_hand_value(1)
    actual_score = sum(c.value for c in game.agent_hands if c is not None)
    ev_error = predicted_ev - actual_score

    return game.get_scores(), ev_error


from multiprocessing import Pool

def run_evaluation(label, agent_class, opponent_class=RandomAgent, n=NUM_GAMES):
    wins = {"agent": 0, "user": 0, "tie": 0}
    ev_errors = []

    with Pool(processes=10) as pool:
        results = pool.starmap(play_game, [(agent_class, opponent_class)] * n)

    for result, ev_err in results:
        wins[result["winner"]] += 1
        ev_errors.append(ev_err)

    print(f"\n=== {label} ({n} games) ===")
    print(f"  Agent wins:    {wins['agent']}/{n} ({100*wins['agent']/n:.1f}%)")
    print(f"  Opponent wins: {wins['user']}/{n}  ({100*wins['user']/n:.1f}%)")
    print(f"  Ties:          {wins['tie']}/{n}")
    print(f"  EV mean error: {np.mean(ev_errors):.2f}")
    print(f"  EV std error:  {np.std(ev_errors):.2f}")
    print(f"  EV MAE:        {np.mean(np.abs(ev_errors)):.2f}")

# def run_evaluation(label, agent_class, opponent_class=RandomAgent, n=NUM_GAMES):
#     wins = {"agent": 0, "user": 0, "tie": 0}
#     ev_errors = []

#     sys.stdout = open(os.devnull, 'w')
#     for i in range(n):
#         result, ev_err = play_game(agent_class, opponent_class)
#         wins[result["winner"]] += 1
#         ev_errors.append(ev_err)

#         # Print progress every 10 games
#         if (i + 1) % 10 == 0:
#             sys.stdout = sys.__stdout__
#             print(f"{label}: {i+1}/{n} games done...", flush=True)
#             sys.stdout = open(os.devnull, 'w')

#     sys.stdout = sys.__stdout__

#     print(f"\n=== {label} ({n} games) ===")
#     print(f"  Agent wins:    {wins['agent']}/{n} ({100*wins['agent']/n:.1f}%)")
#     print(f"  Opponent wins: {wins['user']}/{n}  ({100*wins['user']/n:.1f}%)")
#     print(f"  Ties:          {wins['tie']}/{n}")
#     print(f"  EV mean error: {np.mean(ev_errors):.2f}")   # near 0 = unbiased
#     print(f"  EV std error:  {np.std(ev_errors):.2f}")    # spread of errors
#     print(f"  EV MAE:        {np.mean(np.abs(ev_errors)):.2f}")  # typical accuracy in points

# ─── runs ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    run_evaluation("POMDP vs Random",    BasicPOMDPAgent, RandomAgent,     n=NUM_GAMES)
    run_evaluation("MC+POMDP vs Random", MCPOMDPAgent,    RandomAgent,     n=NUM_GAMES)
    run_evaluation("MC+POMDP vs POMDP",  MCPOMDPAgent,    BasicPOMDPAgent, n=NUM_GAMES)