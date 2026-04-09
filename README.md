# Stool Pigeon

A hidden-information card game AI project built with Pygame. Play against an AI agent in the browser or locally, or run headless evaluations to benchmark agents against each other.

🎮 **Play in your browser:** https://stool-pigeon.netlify.app

---

## Table of Contents

- [About the Game](#about-the-game)
- [Project Structure](#project-structure)
- [Running the Game](#running-the-game)
- [Running Evaluations](#running-evaluations)
- [Agents](#agents)
- [Card Types](#card-types)
- [Game Phases](#game-phases)
- [Credits](#credits)
- [References](#references)

---

## About the Game

Stool Pigeon is a hidden-information card game where players try to minimize the total value of their hand before knocking.

**How a turn works:**
1. Draw a card from the draw pile or discard pile
2. Either swap it with one of your hand cards, or discard it
3. Knock if you think you have the lowest total score

**Your hand:**
- You start with 4 cards
- Your bottom 2 are face-up (known to you at the start)
- Your top 2 are face-down (unknown)

**Winning:**
- When a player knocks, everyone else gets one final turn
- The player with the lowest total hand value wins

**Special rules:**
- Drawing a special action card (Stool Pigeon, Bamboozle, Vendetta, Kingpin) triggers a unique effect instead of a normal keep/discard — see [Card Types](#card-types)
- RAT cards (15 pts) are sticky and can only be removed by a Kingpin action
- MEATBALL cards are worth 0 points

---

## Project Structure

```
Stool-Pidgeon/
├── main.py                          # Web deployment only (async wrapper for Pygbag)
├── StoolPigeonGame.py               # Core game class: logic, rendering, input handling
├── game_state.py                    # GameState and GamePhase (tracks turn/phase/knock)
├── actions.py                       # ActionType enum + Action execution
├── cards.py                         # CardType enum + Card rendering
├── button.py                        # Button UI component
├── title_screen.py                  # Title/difficulty selection screen
├── end_screen.py                    # End screen with final scores
├── evaluate.py                      # Headless evaluation script (runs 500-game trials)
├── agents/
│   ├── random_agent.py             # Random baseline agent
│   ├── heuristic_agent.py          # Rule-based heuristic agent
│   ├── basic_pomdp_agent/
│   │   ├── basic_pomdp_agent.py    # POMDP agent with belief state
│   │   ├── belief_state.py         # Tracks known/unknown cards + expected values
│   │   └── observation.py          # Observation types and belief updates
│   └── monte_carlo_agent/
│       ├── mc_pomdp_agent.py       # MC+POMDP agent (extends BasicPOMDPAgent)
│       └── monte_carlo_agent.py    # Monte Carlo rollout engine
└── images/                          # Card images, backgrounds, buttons
```

**Key entry points:**
| File | Purpose |
|------|---------|
| `StoolPigeonGame.py` | Play the game locally with GUI, or import for scripting |
| `evaluate.py` | Run headless agent evaluations |


---

## Running the Game

**Requirements:** Python 3, Pygame, NumPy

```bash
pip install pygame numpy
python StoolPigeonGame.py
```

This opens the game window. Select a difficulty on the title screen and play.

> `main.py` is only needed for web deployment via Pygbag and not for local play.

---

## Running Evaluations

```bash
python evaluate.py
```

Runs 500-game trials across all agent pairings and prints metrics:

| Matchup | Description |
|---------|-------------|
| Heuristic vs Random | Rule-based agent vs baseline |
| POMDP vs Random | Belief-state agent vs baseline |
| POMDP vs Heuristic | Belief-state agent vs rule-based |
| MC+POMDP vs Random | Monte Carlo agent vs baseline |
| MC+POMDP vs Heuristic | Monte Carlo agent vs rule-based |
| MC+POMDP vs POMDP | Monte Carlo agent vs POMDP |

**Metrics reported per matchup:**
- Win/loss/tie rate
- Average game length (turns)
- Average agent and opponent scores
- Knock accuracy (win rate when the agent knocked)
- EV error (mean, std, MAE) - for agents with a belief state

---

## Agents

Agents are selected in-game via the difficulty menu, or passed directly as `agent_class`:

| Difficulty | Agent | Strategy |
|-----------|-------|----------|
| EASY | `RandomAgent` | Picks uniformly at random from all legal actions |
| MEDIUM | `HeuristicAgent` | Rule-based: keep if card < 5, knock if known sum ≤ 12 |
| HARD | `BasicPOMDPAgent` | Maintains a belief state over unknown cards; uses expected values to decide every action |
| EXPERT | `MCPOMDPAgent` | Extends POMDP with Monte Carlo rollouts to evaluate knock and draw decisions |

### BasicPOMDPAgent (`agents/basic_pomdp_agent/`)

Tracks a probability distribution over all unknown cards (`BeliefState`). Every game event (peek, discard, swap, eliminate) updates the belief via `Observation.update_belief()`.

Decision priority each turn:
1. Knock if expected hand value < 15
2. Peek at the opponent's unknown slot with the highest expected value
3. Keep drawn card if it reduces expected hand value
4. Swap: move a high-value own card out, bring a low-value opponent card in
5. Prefer drawing from discard if the top card is known and better than the worst slot

### MCPOMDPAgent (`agents/monte_carlo_agent/`)

Inherits all POMDP logic and overrides knock and draw decisions with Monte Carlo estimation. For each candidate action, it samples 100 concrete game states from the belief distribution and simulates them to completion using a rollout policy. The action with the highest average outcome (win=1, tie=0, loss=-1) is selected.

---

## Card Types

| Card | Value | Effect |
|------|-------|--------|
| Numbered (1–9) | Face value | None |
| Stool Pigeon | 10 | Peek at any card on the table |
| Bamboozle | 10 | Swap any two face-down cards |
| Vendetta | 10 | Peek at one card, then swap any two |
| Kingpin | 10 | Eliminate one of your own cards, or add a card to your opponent |
| RAT | 15 | No effect; cannot be swapped out (only removed by Kingpin) |
| Meatball | 0 | No effect; worth 0 points |

---

## Game Phases

`GamePhase` (in `game_state.py`) drives all UI and action gating:

| Phase | Description |
|-------|-------------|
| `TITLE_SCREEN` | Difficulty selection |
| `START` | Player views their two face-up cards |
| `DRAW` | Player draws from deck or discard pile |
| `DECIDE` | Player keeps or discards the drawn card |
| `STOOL_PIGEON_PEEK` | Peek at any card |
| `BAMBOOZLE_SELECT` | Select two cards to swap |
| `VENDETTA_PEEK` | Vendetta phase 1: peek |
| `VENDETTA_SWAP` | Vendetta phase 2: swap |
| `KINGPIN_CHOOSE` | Choose: eliminate or add |
| `KINGPIN_ELIMINATE` | Select own card to eliminate |
| `KINGPIN_ADD` | Select opponent slot to add a card |
| `FINAL_TURN` | Post-knock final turn for all players |
| `GAME_OVER` | Scores displayed |

---

## Credits

The original Stool Pigeon card game was designed by **Nate Miller** with artwork by **Jon Yetter**, published by [Barrel Aged Games](https://barrelagedgames.com) (2023). This project is a digital adaptation built for academic research purposes.

---

## References

Yao et al. (2020). *Solving Imperfect Information Poker Games Using Monte Carlo Search and POMDP Models.* IEEE DDCLS.
