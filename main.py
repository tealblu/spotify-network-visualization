# Indigo Hartsell
# 2024-08-31
# Spotify Network Visualization

# Switches
SHOW_VISUALIZATION = True
SHOW_GENRES = True
WRITE_ENTRIES_WITHOUT_GENRE = True
VERBOSE = True

# Globals
DATA_PATH = "data/"
OUTPUT_PATH = "out/"

# Imports
import sys
import os

import pandas as pd
import networkx as nx
from pyvis.network import Network
import matplotlib as mpl
import matplotlib.pyplot as plt

from catppuccin import PALETTE

print("\nSpotify Network Visualization 1.0")
print("Verbose mode is on.") if VERBOSE else None

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
    # Filter out any data that doesn't have necessary fields
    required_columns = ["Spotify ID", "Genres", "Track Name", "Artist Name(s)", "user"]
    data = data.dropna(subset=required_columns).copy()  # Use copy to avoid SettingWithCopyWarning
    
    # Remove special characters from relevant columns
    for column in ["Track Name", "Artist Name(s)", "Genres", "user"]:
        data.loc[:, column] = data[column].str.replace(r'[^\x00-\x7F]+', '', regex=True)
    
    # Resolve duplicate track names with different Spotify IDs
    duplicate_tracks = data[data.duplicated(subset="Track Name", keep=False)]
    if VERBOSE and not duplicate_tracks.empty:
        print(f"Found {len(duplicate_tracks)} duplicate track names. Attempting to resolve.")

    # Ensure no duplicates in index
    data = data.reset_index(drop=True)

    data.loc[duplicate_tracks.index, "Spotify ID"] = data.groupby("Track Name")["Spotify ID"].transform('first')
    
    # Genre categories dictionary
    genre_categories = {
        "Rock & Metal": ["alt-rock", "alternative", "black-metal", "death-metal", "emo", "grindcore", "hard-rock", "hardcore", "heavy-metal", "metal", "metal-misc", "metalcore", "psych-rock", "punk", "punk-rock", "rock", "rock-n-roll", "rockabilly"],
        "Electronic & Dance": ["breakbeat", "chicago-house", "club", "dance", "dancehall", "deep-house", "detroit-techno", "disco", "drum-and-bass", "dub", "dubstep", "edm", "electro", "electronic", "house", "idm", "minimal-techno", "post-dubstep", "progressive-house", "techno", "trance", "trip-hop"],
        "Pop & Indie": ["acoustic", "indie", "indie-pop", "j-pop", "k-pop", "pop", "power-pop", "singer-songwriter", "synth-pop", "indie pop", "buffalo ny indie"],
        "Jazz & Blues": ["blues", "jazz"],
        "Folk & Country": ["bluegrass", "country", "folk", "honky-tonk"],
        "Jazz & Blues": ["blues", "jazz"],
        "Classical & Traditional": ["classical", "opera", "piano"],
        "World & Regional": ["afrobeat", "bossanova", "brazil", "cantopop", "forro", "french", "german", "gospel", "indian", "iranian", "j-dance", "j-idol", "j-rock", "latin", "latino", "malay", "mandopop", "mpb", "pagode", "philippines-opm", "reggaeton", "samba", "sertanejo", "spanish", "swedish", "tango", "turkish", "world-music"],
        "Alternative & Experimental": ["ambient", "chill", "goth", "groove", "industrial", "minimal-techno", "post-dubstep", "psych-rock", "punk", "punk-rock", "shoegaze"],
        "Soundtracks & Themes": ["anime", "comedy", "disney", "holidays", "movies", "romance", "show-tunes", "soundtracks"],
        "Miscellaneous": ["children", "happy", "rainy-day", "road-trip", "sad", "sleep", "study", "summer", "work-out", "new-age", "new-release", "party"]
    }
    
    # Flatten genre categories
    genre_to_category = {genre: category for category, genres in genre_categories.items() for genre in genres}
    
    # Replace genres with categories or set to miscellaneous if not found
    def map_genres(genre_str):
        genres = genre_str.split(",")
        mapped_genres = []
        missing_genres = []
        for genre in genres:
            print(genre) if VERBOSE else None
            if genre in genre_to_category.keys():
                mapped_genres.append(genre_to_category[genre])
            else:
                # check if missing genre is already in list
                if genre not in missing_genres:
                    missing_genres.append(genre)
                mapped_genres.append("Unknown")

        if WRITE_ENTRIES_WITHOUT_GENRE and missing_genres:
            with open(OUTPUT_PATH + "missing_genres.txt", "a") as f:
                f.write(f"{missing_genres}\n")                
        return ", ".join(set(mapped_genres))
    
    data["Genres"] = data["Genres"].apply(map_genres)
    
    # Remove entries without matching genre
    data = data[data["Genres"] != ""]

    # Sort genre lists alphabetically
    data["Genres"] = data["Genres"].apply(lambda x: ", ".join(sorted(x.split(", "))))
    
    if VERBOSE:
        print("Unique genres in dataset:")
        print(data["Genres"].unique())

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
        nodes.append({"id": user, "type": "user", "label": user, "color": PALETTE.mocha.colors.overlay0.hex, "size": 30, "bipartite": 0})

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

        nodes.append({"id": spotify_id, "type": "track", "label": track_labels[index], "genre": genre, "color": genre_color.hex, "size": 15, "bipartite": 1})

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
            nodes.append({"id": genre, "type": "genre", "label": genre, "color": genre_colors[genres.index(genre)].hex, "size": 5, "bipartite": 20})

        # Create edges for genres
        for spotify_id in spotify_ids:
            track_data = data[data["Spotify ID"] == spotify_id]
            genre = track_data["Genres"].tolist()[0]
            edges.append({"source": spotify_id, "target": genre, "color": genre_colors[genres.index(genre)].hex})

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
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

# End of file