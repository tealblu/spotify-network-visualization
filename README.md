# Spotify Network Visualization

This project generates an interactive network visualization that shows the similarity between music genres based on your liked songs from Spotify. The primary script, `render_spotify_network.py`, processes your Spotify data and creates an HTML file with the network visualization.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Notes](#notes)

## Features

- **Genre Mapping**: Automatically matches genres to your liked songs using a predefined mapping file (`genre_mapping.json`). This file can be updated using the `genre_resolution.py` script.
- **Network Visualization**: Generates a visual network of your music tastes with edges representing similarity between genres.
- **HTML Output**: Creates a standalone `network.html` file that can be viewed in any browser.

## Requirements

- Python 3.x
- The following Python packages:
  - `networkx`
  - `pandas`
  - `pyvis`
  - `catppuccin`

## Notes
  - To use this tool, your spotify data must already be present as a .CSV file in the `data` folder. Use [this link](https://exportify.net/) to download your spotify data.
