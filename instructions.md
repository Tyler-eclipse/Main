# Chess Engine Project (PyGame + Minimax AI)
## Overview

This project implements a modular chess system featuring a playable graphical interface and a sophisticated benchmarking arena. It utilizes a classical Minimax AI with Alpha-Beta pruning for deterministic move calculation, which can be played against directly or compared against probabilistic Large Language Models (LLMs).
Project Structure

The project is modularized into the following files to separate logic from the interface:

    main.py: The entry point for the GUI application.

    board.py: The core logic engine handling board representation (8x8 list), legal move generation, and game-state tracking.

    engine.py: Implements the Minimax search, Alpha-Beta pruning, move ordering, and heuristic evaluation.

    ui.py: Manages PyGame asset loading and the drawing of the board and pieces.

    move.py: Contains the Move dataclass with support for promotions, castling, and en passant.

    constants.py: Stores piece values used for evaluation.

    llm_benchmark/: A standalone suite for running headless "Arena" matches between the engine and external LLMs.

## Feature 1: Graphical User Interface (GUI)

The GUI is designed for human-vs-engine play, providing real-time visual feedback and interactive controls.
Key GUI Features

    Full Move Support: Includes logic for castling, en passant, and pawn promotion.

    Interactive UI: Provides legal move highlighting and highlights the currently selected piece.

    Performance Telemetry: Displays the engine's "think time" in milliseconds (ms) after every move.

    Draw Logic: Automatically detects draws by 50-move rule, threefold repetition, and insufficient material.

## GUI Controls

    Mouse Click: Select a piece to see legal moves; click a destination square to move.

    Keys 1, 2, 3: Dynamically set the AI search depth to adjust difficulty levels.

    U Key: Undo the last turn (reverts both the AI and player moves).

    R Key: Reset the board to the starting position.

## Feature 2: LLM Benchmarking Arena

The llm_benchmark suite is a headless framework used to evaluate classical engine performance against modern LLMs (via Ollama).
How the Arena Works

    Headless Competition: The arena.py script runs games without a GUI, alternating colors to ensure fairness.

    Validation & Fallbacks: Every LLM move is validated. If the LLM suggests an illegal move, the system attempts a "repair pass" or falls back to a random legal move.

    Statistical Summary: Reports W-D-L records, average plies per game, and comparative "think times" between the classical engine and the LLM.

## Running a Benchmark

Execute the following command from the project root (requires Ollama to be installed and running):
Bash

python llm_benchmark/arena.py --games 10 --engine-depth 2 --llm-command "python llm_benchmark/ollama_uci_player.py --model llama3.1:8b"

## Setup Instructions

    Install Python: Version 3.10 or higher is recommended.

    Install Dependencies:
    Bash

    pip install pygame

    Asset Requirement: Ensure piece images (e.g., white-pawn.png) are located in a folder named pieces-basic-png or in the root directory.

    Ollama Setup (Optional): To use the benchmark, install Ollama and pull a model: ollama pull llama3.1:8b.