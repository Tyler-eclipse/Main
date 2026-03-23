# Chess Engine Project (PyGame + Minimax AI)

## Overview

This project implements a **basic chess engine** with a graphical interface using **PyGame** and an AI opponent using **Minimax with Alpha-Beta pruning**.  

The project is modularized into the following files:

- `move.py` → `Move` dataclass and move-related helper functions  
- `board.py` → Board representation, legal/pseudo-legal move generation, evaluation  
- `engine.py` → Minimax/Alpha-Beta search and AI move selection  
- `main.py` → PyGame GUI, player interaction, game loop  
- `game_state.py` → Optional: track castling rights, en passant, and move history  

**Key features:**

- Legal move generation for all pieces  
- Special moves: castling, en passant, pawn promotion  
- AI opponent with adjustable search depth (difficulty levels)  
- 2-player mode support  
- Undo functionality  
- Basic evaluation function for AI  

---

## Setup Instructions

1. **Install Python (≥3.10 recommended)**  
   [Download Python](https://www.python.org/downloads/)

2. **Install Dependencies**  

```bash
pip install pygame