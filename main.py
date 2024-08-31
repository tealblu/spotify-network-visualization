# Indigo Hartsell
# 2024-08-31
# Spotify Network Visualization

print("\nSpotify Network Visualization 1.0")

# Imports
import sys
import os

import pandas as pd
import networkx as nx
from pyvis.network import Network
import matplotlib as mpl
import matplotlib.pyplot as plt

from catppuccin import PALETTE

# Switches
SHOW_VISUALIZATION = True
SHOW_GENRES = False
VERBOSE = True
print("Verbose mode is on.") if VERBOSE else None

# Globals
DATA_PATH = "data/"
OUTPUT_PATH = "out/"

def load_data_from_csv():
    # Get filenames from datapath
    filenames = os.listdir(DATA_PATH)
    
    # Load data from each file
    data_list = []
    for filename in filenames:
        print("Loading data from file: " + filename)
        data = pd.read_csv(DATA_PATH + filename)

        # Get the name of the spotify user from the first part of the filename
        user = filename.split("_")[0]

        # Add user as an additional column in the dataframe
        data["user"] = user

        data_list.append(data)

        print("Data sample for " + user + ":") if VERBOSE else None
        print(data.head()) if VERBOSE else None

    # Concatenate all dataframes into one
    combined_data = pd.concat(data_list)
    return combined_data

def clean_data(data):
    # Filter out any data that doesn't have a spotify_id
    data = data[data["Spotify ID"].notna()]

    # Filter out any data that doesn't have a genre
    data = data[data["Genres"].notna()]

    # Filter out any data that doesn't have a track name
    data = data[data["Track Name"].notna()]

    # Filter out any data that doesn't have an artist name
    data = data[data["Artist Name(s)"].notna()]

    # Filter out any data that doesn't have a user
    data = data[data["user"].notna()]

    # Remove special characters and foreign characters from track names
    data["Track Name"] = data["Track Name"].str.replace(r'[^\x00-\x7F]+', '', regex=True)

    # Remove special characters from artist names
    data["Artist Name(s)"] = data["Artist Name(s)"].str.replace(r'[^\x00-\x7F]+', '', regex=True)

    # Remove special characters from genres
    data["Genres"] = data["Genres"].str.replace(r'[^\x00-\x7F]+', '', regex=True)

    # Remove special characters from user names
    data["user"] = data["user"].str.replace(r'[^\x00-\x7F]+', '', regex=True)

    # Search for duplicate track names with different Spotify IDs and combine them
    duplicate_tracks = data[data.duplicated(subset="Track Name", keep=False)]
    print(f"Found {len(duplicate_tracks)} duplicate track names. Attempting to resolve.") if VERBOSE and len(duplicate_tracks) > 0 else None

    for index, row in duplicate_tracks.iterrows():
        # Get all Spotify IDs for the track name
        track_name = row["Track Name"]
        spotify_ids = data[data["Track Name"] == track_name]["Spotify ID"].unique().tolist()
        
        if len(spotify_ids) == 1:
            continue

        print(f"Found {len(spotify_ids)} Spotify IDs for track name '{track_name}': {spotify_ids}") if VERBOSE else None

        # Replace all Spotify IDs with the first one
        first_spotify_id = spotify_ids[0]
        data.loc[data["Track Name"] == track_name, "Spotify ID"] = first_spotify_id
        print(f"-> Replacing all Spotify IDs with '{first_spotify_id}' for track name '{track_name}'.") if VERBOSE else None

    # Dictionary of genre categories
    genre_categories = {
        "Rock & Metal": ["alt-rock", "alternative", "black-metal", "death-metal", "emo", "grindcore", "hard-rock", "hardcore", "heavy-metal", "metal", "metal-misc", "metalcore", "psych-rock", "punk", "punk-rock", "rock", "rock-n-roll", "rockabilly"],
        "Electronic & Dance": ["breakbeat", "chicago-house", "club", "dance", "dancehall", "deep-house", "detroit-techno", "disco", "drum-and-bass", "dub", "dubstep", "edm", "electro", "electronic", "house", "idm", "minimal-techno", "post-dubstep", "progressive-house", "techno", "trance", "trip-hop"],
        "Pop & Indie": ["acoustic", "indie", "indie-pop", "j-pop", "k-pop", "pop", "power-pop", "singer-songwriter", "synth-pop"],
        "Folk & Country": ["bluegrass", "country", "folk", "honky-tonk"],
        "Jazz & Blues": ["blues", "jazz"],
        "Classical & Traditional": ["classical", "opera", "piano"],
        "World & Regional": ["afrobeat", "bossanova", "brazil", "cantopop", "forro", "french", "german", "gospel", "indian", "iranian", "j-dance", "j-idol", "j-rock", "latin", "latino", "malay", "mandopop", "mpb", "pagode", "philippines-opm", "reggaeton", "samba", "sertanejo", "spanish", "swedish", "tango", "turkish", "world-music"],
        "Alternative & Experimental": ["ambient", "chill", "goth", "groove", "industrial", "minimal-techno", "post-dubstep", "psych-rock", "punk", "punk-rock", "shoegaze"],
        "Soundtracks & Themes": ["anime", "comedy", "disney", "holidays", "movies", "romance", "show-tunes", "soundtracks"],
        "Miscellaneous": ["children", "happy", "rainy-day", "road-trip", "sad", "sleep", "study", "summer", "work-out", "new-age", "new-release", "party"]
    }
    
    # Pivoting the dictionary to map genres to their larger category
    genre_to_category = {}
    for category, genres in genre_categories.items():
        for genre in genres:
            genre_to_category[genre] = category
    
    # Replace the list of genres with one string containing the genre category
    data["Genres"] = data["Genres"].apply(lambda x: ", ".join([genre_to_category[genre] for genre in x.split(",") if genre in genre_to_category]))

    # Collapse entries with multiple of the same genre
    data["Genres"] = data["Genres"].apply(lambda x: ", ".join(set(x.split(", "))))

    # Sort each entry's genre list alphabetically
    data["Genres"] = data["Genres"].apply(lambda x: ", ".join(sorted(x.split(", "))))

    # Set entries without genre to miscellaneous
    data["Genres"] = data["Genres"].apply(lambda x: "Miscellaneous" if x == "" else x)

    # Print genres for debugging
    print("Unique genres in dataset:") if VERBOSE else None
    print(data["Genres"].unique()) if VERBOSE else None

    return data
    
def create_nodes_and_edges(data):
    # Extract unique users and Spotify IDs from dataframe
    users = data["user"].unique().tolist()
    spotify_ids = data["Spotify ID"].unique().tolist()

    # Create labels for tracks
    track_labels = []
    for spotify_id in spotify_ids:
        track_data = data[data["Spotify ID"] == spotify_id]

        # Check if track_data is empty
        if track_data.empty:
            print(f"Warning: No data found for Spotify ID {spotify_id}. Skipping...") if VERBOSE else None
            track_labels.append("Unknown - Unknown")
            continue

        artist = track_data["Artist Name(s)"].iloc[0]
        track_name = track_data["Track Name"].iloc[0]
        track_labels.append(track_name + "\n" + artist)

    # Create nodes
    nodes = []
    for user in users:
        nodes.append({"id": user, "type": "user", "label": user, "color": PALETTE.mocha.colors.overlay0.hex, "size": 15, "bipartite": 0})

    # Get list of colors from palette
    colors = []
    for color in PALETTE.mocha.colors:
        colors.append(color) if color.accent else None

    # Get genres from data
    genres = data["Genres"].unique().tolist()

    # Create palette for genres with len(genres) colors
    genre_colors = []
    legend = {}
    for i in range(len(genres)):
        genre_colors.append(colors[i % len(colors)])
        print("Genre " + genres[i] + " has color " + genre_colors[i].name) if VERBOSE else None

    # Create nodes for tracks
    for spotify_id in spotify_ids:
        index = list(spotify_ids).index(spotify_id)
        
        # Get genre for track
        track_data = data[data["Spotify ID"] == spotify_id]
        genre = track_data["Genres"].iloc[0]
        genre_color = genre_colors[genres.index(genre)]

        nodes.append({"id": spotify_id, "type": "track", "label": track_labels[index], "genre": genre, "color": genre_color.hex, "size": 3, "bipartite": 1})

    # Create edges by looping thru spotify ids and users
    edges = []
    for spotify_id in spotify_ids:
        track_data = data[data["Spotify ID"] == spotify_id]
        users = track_data["user"].tolist()
        for user in users:
            edges.append({"source": user, "target": spotify_id})
    
    if SHOW_GENRES:
        # Create nodes for genres
        for genre in genres:
            nodes.append({"id": genre, "type": "genre", "label": genre, "color": legend[genre].hex, "size": 5, "bipartite": 2})

        # Create edges for genres
        for spotify_id in spotify_ids:
            track_data = data[data["Spotify ID"] == spotify_id]
            genres = track_data["Genres"]
            for genre in genres:
                edges.append({"source": spotify_id, "target": genre, "color": legend[genre].hex})

    print("Created " + str(len(nodes)) + " nodes and " + str(len(edges)) + " edges.") if VERBOSE else None

    return nodes, edges

def visualize_network(nodes, edges):
    # Create a new graph
    G = nx.Graph()

    # Add nodes and edges to the graph
    for node in nodes:
        G.add_node(node["id"], label=node["label"], type=node["type"], size=node["size"], bipartite=node["bipartite"], color=node["color"])
    
    for edge in edges:
        G.add_edge(edge["source"], edge["target"])

    # Create a network visualization
    N = Network("1000px", "1000px", notebook=False, directed=False, bgcolor=PALETTE.mocha.colors.mantle.hex, font_color=PALETTE.mocha.colors.text.hex)
    N.from_nx(G)

    # Configure the network visualization
    N.barnes_hut(spring_strength=0.15)
    N.show_buttons(filter_=True)

    # Show visualization
    N.show(OUTPUT_PATH + "network.html", notebook=False) if SHOW_VISUALIZATION else None
    print("Network visualization displayed in browser.") if VERBOSE and SHOW_VISUALIZATION else None

def main():
    print("\nPlease wait while the visualization is created...")

    try:
        print("Loading data...")
        data = load_data_from_csv()
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    try:
        print("Cleaning data...")
        data = clean_data(data)
        print("Data cleaned successfully.")
    except Exception as e:
        print(f"Error cleaning data: {e}")
        return

    try:
        print("\nPreparing nodes and edges...")
        nodes, edges = create_nodes_and_edges(data)
        print("Nodes and edges prepared successfully.")
    except Exception as e:
        print(f"Error preparing nodes and edges: {repr(e)}")
        return

    try:
        print("\nCreating network visualization...")
        visualize_network(nodes, edges)
        print("Network visualization created successfully.")
    except Exception as e:
        print(f"Error creating network visualization: {repr(e)}")
        return

    print("\nProgram complete.")

    

# Main
if __name__ == "__main__":
    main()