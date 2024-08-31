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
        nodes.append({"id": user, "type": "user", "label": user})

    for spotify_id in spotify_ids:
        index = list(spotify_ids).index(spotify_id)
        nodes.append({"id": spotify_id, "type": "track", "label": track_labels[index], "genre": data[data["Spotify ID"] == spotify_id]["Genres"].iloc[0]})

    # Create edges by looping thru spotify ids and users
    edges = []
    for spotify_id in spotify_ids:
        track_data = data[data["Spotify ID"] == spotify_id]
        users = track_data["user"].tolist()
        for user in users:
            edges.append({"source": user, "target": spotify_id})

    print("Created " + str(len(nodes)) + " nodes and " + str(len(edges)) + " edges.") if VERBOSE else None

    return nodes, edges

def visualize_network(nodes, edges):
    # Create a new graph
    G = nx.Graph()

    user_nodes = [node for node in nodes if node["type"] == "user"]
    track_nodes = [node for node in nodes if node["type"] == "track"]

    # Add nodes and edges to the graph
    for node in user_nodes:
        G.add_node(node["id"], label=node["label"], type="user", bipartite=0, color=PALETTE.mocha.colors.mauve.hex)
    
    for node in track_nodes:
        G.add_node(node["id"], label=node["label"], type="track", bipartite=1, color=PALETTE.mocha.colors.blue.hex)
    
    for edge in edges:
        G.add_edge(edge["source"], edge["target"])

    # Create a network visualization
    N = Network("1000px", "1000px", notebook=False, directed=False, bgcolor=PALETTE.mocha.colors.mantle.hex, font_color=PALETTE.mocha.colors.text.hex)
    N.from_nx(G)

    # Configure the network visualization
    N.barnes_hut(spring_strength=0.15)
    N.show_buttons(filter_=True)

    # Show visualization
    N.show(OUTPUT_PATH + "network.html", notebook=False)
    print("Network visualization displayed in browser.") if VERBOSE else None

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
        print(f"Error preparing nodes and edges: {e}")
        return

    try:
        print("\nCreating network visualization...")
        visualize_network(nodes, edges)
        print("Network visualization created successfully.")
    except Exception as e:
        print(f"Error creating network visualization: {e}")
        return

    print("\nProgram complete.")

    

# Main
if __name__ == "__main__":
    main()