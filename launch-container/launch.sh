#!/usr/bin/env bash

# Allow X11 connections and launch the Snake game in Docker with GUI display.
#
# Prerequisites: XQuartz running (macOS), xhost available, Docker image built.
# Usage: run from repository root:  bash docker-gui/run-snake-with-display.sh

# Allow connections to the X display (required for Docker to forward the GUI).
export DISPLAY=:0
xhost +

# Launch the container with display forwarding (no demo timeout).
docker run --rm \
  -e DISPLAY=host.docker.internal:0 \
  -e SDL_VIDEODRIVER=x11 \
  -e SDL_AUDIODRIVER=dummy \
  -e SNAKE_DEMO_SECONDS=0 \
  jcam989/snake-pygame:0.1.1-arm64
