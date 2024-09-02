# Spotify Network Visualization

This project generates an interactive network visualization that shows the similarity between music genres based on your liked songs from Spotify. The primary script, `render_spotify_network.py`, processes your Spotify data and creates an HTML file with the network visualization.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Notes](#notes)

## Features

- **Genre Mapping**: Automatically matches genres to your liked songs using a predefined mapping file (`genre_mapping.json`). This file can be updated using the `genre_resolution.py` script.
- **Network Visualization**: Generates a visual network of your music tastes with edges representing similarity between genres. View the visualization by running `render_spotify_network.py`
- **HTML Output**: Creates a standalone `network.html` file that can be viewed in any browser.

## Requirements

- Python 3.x
- The following Python packages:
  - `networkx`
  - `pandas`
  - `pyvis`
  - `catppuccin`

You can install these requirements using pip:
```bash
pip install -r requirements.txt
```

## Notes
  - To use this tool, your spotify data must already be present as a .CSV file in the `data` folder. Use [this link](https://exportify.net/) to download your spotify data.
    - Format the output csv file like this: `YOURNAME_liked_songs.csv`.
  - Changing the switches at the top of `render_spotify_network.py` will change what is rendered.
  - Try rendering multiple data sets at one time :)
