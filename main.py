# Indigo Hartsell
# 2024-08-31
# Spotify Network Visualization

# Imports
import sys
import os

import pandas as pd
import networkx as nx
import matplotlib as mpl
import matplotlib.pyplot as plt

from catppuccin import PALETTE

# Globals
DATA_PATH = "data/"

def load_data_from_csv():
    # Get filenames from datapath
    filenames = os.listdir(DATA_PATH)
    
    # Load data from each file
    data_list = []
    for filename in filenames:
        print("\nLoading data from file: " + filename)
        data = pd.read_csv(DATA_PATH + filename)

        # Get the name of the spotify user from the first part of the filename
        user = filename.split("_")[0]

        # Add user as an additional column in the dataframe
        data["user"] = user

        data_list.append(data)

        print("Data sample for " + user + ":")
        print(data.head())

    # Concatenate all dataframes into one
    combined_data = pd.concat(data_list)
    return combined_data

def create_nodes_and_edges(data):
    # Filter out any data that doesn't have a spotify_id
    data = data[data["Spotify ID"].notna()]

    # Extract unique users and Spotify IDs from dataframe
    users = data["user"].unique().tolist()
    spotify_ids = data["Spotify ID"].unique().tolist()
    
    # Get labels for tracks - artist and track name
    track_labels = []
    for spotify_id in spotify_ids:
        track_data = data[data["Spotify ID"] == spotify_id]

        # Check if track_data is empty
        if track_data.empty:
            print(f"Warning: No data found for Spotify ID {spotify_id}. Skipping...")
            track_labels.append("Unknown - Unknown")
            continue

        artist = track_data["Artist Name(s)"].iloc[0]
        track_name = track_data["Track Name"].iloc[0]
        track_labels.append(artist + " - " + track_name)

    # Replace special characters in labels (#, $, %, &)
    track_labels = [label.replace("#", "sharp").replace("$", "dollar").replace("%", "percent").replace("&", "and") for label in track_labels]

    # Create nodes
    nodes = []
    for user in users:
        nodes.append({"id": user, "type": "user", "label": user})

    for spotify_id in spotify_ids:
        index = list(spotify_ids).index(spotify_id)
        nodes.append({"id": spotify_id, "type": "track", "label": track_labels[index]})

    # Create edges by looping thru spotify ids and users
    edges = []
    for spotify_id in spotify_ids:
        track_data = data[data["Spotify ID"] == spotify_id]
        users = track_data["user"].tolist()
        for user in users:
            edges.append({"source": user, "target": spotify_id})

    return nodes, edges

def visualize_network(nodes, edges):
    # Create a new graph
    G = nx.Graph()

    user_nodes = [node for node in nodes if node["type"] == "user"]
    track_nodes = [node for node in nodes if node["type"] == "track"]

    # Add nodes and edges to the graph
    G.add_nodes_from([node["id"] for node in user_nodes], type="user", bipartite=0, color=PALETTE.mocha.colors.mauve)
    G.add_nodes_from([node["id"] for node in track_nodes], type="track", bipartite=1, color=PALETTE.mocha.colors.blue)
    G.add_edges_from([(edge["source"], edge["target"]) for edge in edges])

    # Configure plot
    mpl.style.use(PALETTE.mocha.identifier)
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 12))
    plt.rcParams['text.usetex'] = False

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, nodelist=[node["id"] for node in user_nodes], node_color="b", node_size=100, alpha=0.8)
    nx.draw_networkx_nodes(G, pos, nodelist=[node["id"] for node in track_nodes], node_color="r", node_size=100, alpha=0.8)

    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.5)

    # Draw labels
    labels = {node["id"]: node["label"] for node in nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=6)
    
    # Save the graph to a file
    plt.savefig("out/network.png")
    print("Network visualization saved to 'out/network.png'.")

    # Show the plot
    plt.show()

def main():
    print("Getting ready to load data...")
    data = load_data_from_csv()
    print("Data loaded successfully.")

    print("\nPreparing nodes and edges...")
    nodes, edges = create_nodes_and_edges(data)
    print("Nodes and edges prepared successfully.")

    print("\nCreating network visualization...")
    visualize_network(nodes, edges)

    

# Main
if __name__ == "__main__":
    main()