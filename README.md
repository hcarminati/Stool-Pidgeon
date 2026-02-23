# Stool Pigeon

A card game AI project built with Pygame. Play against an AI agent or watch agents compete against each other.

🎮 **Play in your browser:** https://fancy-marshmallow-b82433.netlify.app

---

## About

Stool Pigeon is a hidden information card game where players try to minimize the total value of their hand before knocking. The deck includes numbered cards as well as special action cards (Stool Pigeon, Bamboozle, Vendetta, and Kingpin) each of which triggers a unique interactive effect.

This project implements a game environment and a series of AI agents of increasing sophistication, from a random baseline to a POMDP-based agent using Monte Carlo search.

---

## Project Structure

```
├── StoolPigeonGame.py     # Main game loop and rendering
├── game_state.py          # Game phase and state tracking
├── actions.py             # Action definitions and execution
├── cards.py               # Card types and rendering
├── button.py              # Button UI component
├── agents/
│   └── random_agent.py    # Random baseline agent
└── images/                # Card and background assets
```

---

## Running the Game

**Requirements:** Python 3, Pygame

```bash
pip install pygame
python StoolPigeonGame.py
```

To run without the GUI:
```python
game = StoolPigeonGame(GUI=False, agent_class=RandomAgent)
```

---

## Agents

| Agent | Status | Description |
|-------|--------|-------------|
| `RandomAgent` | ✅ Complete | Selects randomly from legal actions |
| `HeuristicAgent` | 📅 Planned | Rule-based decisions on hand strength |
| `POMDPAgent` | 📅 Planned | Belief state + Bayesian inference |
| `POMDPAgent` + Monte Carlo | 📅 Planned | Extends POMDP with Monte Carlo rollouts to estimate action values |

---

## Credits

The original Stool Pigeon card game was designed by **Nate Miller** with artwork by **Jon Yetter**, published by [Barrel Aged Games](https://barrelagedgames.com) (2023). This project is a digital adaptation built for academic research purposes.

---

## References

Yao et al. (2020). *Solving Imperfect Information Poker Games Using Monte Carlo Search and POMDP Models.* IEEE DDCLS.
