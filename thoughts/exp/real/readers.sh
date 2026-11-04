#!/bin/zsh
# Run the five fixed readers (review RM-7: one reader set) on image runs, or on text with MODE=text.
# usage: ./readers.sh run1 run2 ...        MODE=text RAW=1 ./readers.sh lb3_s6_hotpot
cd "${0:A:h}"
script=run_openrouter.py; [[ "$MODE" == text ]] && script=run_text.py
for m in google/gemini-3.5-flash-lite qwen/qwen3-vl-235b-a22b-instruct meta-llama/llama-4-maverick; do
  MODEL=$m python3 $script "$@" &
done
EFFORT=minimal MAXTOK=8000 MODEL=openai/gpt-6-luna python3 $script "$@" &
if [[ "$MODE" == text ]]; then MODEL=minimax python3 run_text.py "$@"; else python3 run_minimax.py "$@"; fi
wait
# one retry pass for transport errors / rate-limit empties
for m in google/gemini-3.5-flash-lite qwen/qwen3-vl-235b-a22b-instruct meta-llama/llama-4-maverick; do
  RETRY=1 MODEL=$m python3 $script "$@" &
done
RETRY=1 EFFORT=minimal MAXTOK=8000 MODEL=openai/gpt-6-luna python3 $script "$@" &
if [[ "$MODE" == text ]]; then RETRY=1 MODEL=minimax python3 run_text.py "$@"; else RETRY=1 python3 run_minimax.py "$@"; fi
wait
echo DONE "$@"
