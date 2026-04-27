# LLM Benchmark (Separate from Game UI)

This folder is a standalone, headless benchmark runner for comparing:

- your alpha-beta chess engine (`engine.py`)
- an external LLM move generator (via shell command)

It does not modify your `main.py` gameplay flow.

## How it works

- Alternates colors each game so both sides are fair.
- Validates every LLM move against legal moves.
- If LLM returns invalid output, retries (`--llm-retries`), then falls back to a random legal move.
- Reports engine W-D-L, average game length, think times, and LLM invalid/fallback counts.

## Usage

From project root:

```bash
python llm_benchmark/arena.py --games 10 --engine-depth 2 --llm-command "<your_command_here>"
```

Required:

- `--llm-command`: command that reads prompt from stdin and prints one UCI move (e.g. `e2e4`).

Useful options:

- `--llm-timeout-s 20`
- `--llm-retries 1`
- `--max-plies 200`
- `--seed 42`

## Command contract

Your command must:

1. read text prompt from stdin
2. print one legal UCI move on stdout (`e2e4`, `e7e8q`, etc.)

The runner extracts the first UCI token from stdout.

## Ollama Integration (No API Cost)

1. Install Ollama and start it:

- Install: [https://ollama.com/download](https://ollama.com/download)
- Verify: `ollama --version`

2. Pull a local model:

```bash
ollama pull llama3.1:8b
```

3. Run benchmark using the included Ollama adapter:

```bash
python llm_benchmark/arena.py --games 10 --engine-depth 2 --llm-timeout-s 20 --llm-command "python llm_benchmark/ollama_uci_player.py --model llama3.1:8b --timeout-s 8"
```

You can change `--model` to any model you have pulled locally.

