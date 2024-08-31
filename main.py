# Indigo Hartsell
# 2024-08-31
# Spotify Network Visualization

# Imports
import sys
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Globals
DATA_PATH = "data/"

def load_data_from_csv():
    # Get filenames from datapath
    filenames = os.listdir(DATA_PATH)
    
    # Load data from each file\
    data_list = []
    for filename in filenames:
        print("\nLoading data from file: " + filename)
        data = pd.read_csv(DATA_PATH + filename)

        # Get the name of the spotify user from the first part of the filename
        user = filename.split("_")[0]

        # Add user as an additional column in the dataframe
        data["user"] = user
        data_list.append(data)

    # Concatenate all dataframes into one
    combined_data = pd.concat(data_list)
    return combined_data

def create_nodes_and_edges(data):
    # Extract unique users and Spotify IDs from dataframe
    users = data["user"].unique()
    spotify_ids = data["Spotify ID"].unique()

    # Create nodes
    nodes = []
    for user in users:
        nodes.append({"id": user, "type": "user"})

    for spotify_id in spotify_ids:
        nodes.append({"id": spotify_id, "type": "track"})

    # Create edges
    edges = []
    for index, row in data.iterrows():
        edges.append({"source": row["user"], "target": row["Spotify ID"]})

    return nodes, edges

def visualize_network(nodes, edges):
    # Create a new graph
    G = nx.Graph()

    # Add nodes and edges to the graph
    for node in nodes:
        G.add_node(node["id"], type=node["type"])

    for edge in edges:
        G.add_edge(edge["source"], edge["target"])

    # Draw the graph
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=False, font_weight='bold')
    
    # Save the graph to a file
    plt.savefig("out/network.png")

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