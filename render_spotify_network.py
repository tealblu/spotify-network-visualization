# Indigo Hartsell
# 2024-08-31
# Spotify Network Visualization

# Imports
import sys
import os

import pandas as pd
import networkx as nx
from pyvis.network import Network

from catppuccin import PALETTE

# Switches
SHOW_VISUALIZATION =          True # Set to False to disable opening the visualization in a browser
SHOW_GENRES =                 True # Set to False to disable showing genre nodes
SHOW_SONGS =                  True # Set to False to disable showing song nodes
SHOW_GENRE_USERS =            True # Set to False to disable showing genre > user connections
WRITE_ENTRIES_WITHOUT_GENRE = True # Set to False to disable writing entries without genre to a file
VERBOSE =                     True # Set to False to disable verbose output

# Check to make sure switches are compatible
if not SHOW_GENRES and not SHOW_SONGS and not SHOW_GENRE_USERS:
    print("Error: At least one of SHOW_GENRES, SHOW_SONGS, or SHOW_GENRE_USERS must be set to True.")
    sys.exit(1)

if SHOW_GENRE_USERS and not SHOW_GENRES:
    print("Error: SHOW_GENRE_USERS cannot be set to True if SHOW_GENRES is set to False.")
    sys.exit(1)

# Globals
DATA_PATH = "data/"
OUTPUT_PATH = "out/"

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

def genre_to_category(genre):
    genre_mapping = pd.read_json("genre_mapping.json", typ="series")
    genre_to_category = genre_mapping.to_dict()
    return genre_to_category.get(genre, "Unknown")

def get_category_list():
    genre_mapping = pd.read_json("genre_mapping.json", typ="series")
    genre_to_category = genre_mapping.to_dict()
    categories = list(genre_to_category.values())
    return categories

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
    
    # Get list of genres for each track
    data["Genres"] = data["Genres"].str.split(", ")

    # Create a new column for the primary genre of each track (first genre in list)
    data["Primary Genre"] = data["Genres"].apply(lambda x: x[0].split(",")[0])

    # Create a new column for the category of each genre
    data["Category"] = data["Primary Genre"].apply(genre_to_category)

    # Set category to "Unknown" if genre is not in the dictionary
    data.loc[data["Category"].isnull(), "Category"] = "Unknown"

    # Write entries without category to a file
    if WRITE_ENTRIES_WITHOUT_GENRE:
        entries_without_genre = data[data["Category"] == "Unknown"]
        if not entries_without_genre.empty:
            entries_without_genre.to_csv(OUTPUT_PATH + "entries_without_genre.csv", index=False)
            print("Entries without genre written to file.")
        else:
            print("No entries without genre found.")

    return data

    
def create_nodes_and_edges(data):
    # Extract unique users and Spotify IDs from dataframe
    users = data["user"].unique().tolist()
    spotify_ids = data["Spotify ID"].unique().tolist()

    nodes = []
    edges = []

    # Create nodes for users
    for user in users:
        nodes.append({"id": user, "type": "user", "label": user, "color": PALETTE.mocha.colors.overlay0.hex, "size": 30, "bipartite": 0})

    # Create labels for tracks
    track_labels = {}
    for spotify_id in spotify_ids:
        track_data = data[data["Spotify ID"] == spotify_id]

        # Check if track_data is empty
        if track_data.empty:
            print(f"Warning: No data found for Spotify ID {spotify_id}. Skipping...") if VERBOSE else None
            track_labels.append("Unknown - Unknown")
            continue

        artist = track_data["Artist Name(s)"].iloc[0]
        track_name = track_data["Track Name"].iloc[0]
        track_labels[spotify_id] = track_name + "\n" + artist

    # Get list of colors from palette
    colors = []
    for color in PALETTE.mocha.colors:
        colors.append(color) if color.accent else None

    # Get list of categories
    categories = get_category_list() + ["Unknown"]

    # Create palette for categories with len(categories) colors modulated from the palette
    category_colors = [colors[i % len(colors)] for i in range(len(categories))]

    # Create nodes and edges for tracks
    if SHOW_SONGS:
        for spotify_id in spotify_ids:
            # Get data for track
            track_data = data[data["Spotify ID"] == spotify_id]
            label = track_labels[spotify_id]
            genre = track_data["Primary Genre"].iloc[0]
            category = track_data["Category"].iloc[0]
            color = category_colors[categories.index(category)].hex
            users = track_data["user"].tolist()

            # Create node for track
            nodes.append({"id": spotify_id, "type": "track", "label": label, "genre": genre, "color": color, "size": 2, "bipartite": 1})

            # Create edges between users and tracks
            for user in users:
                edges.append({"source": user, "target": spotify_id, "color": PALETTE.mocha.colors.overlay1.hex, "length": 0.5})
    
    # Create nodes and edges for genres
    if SHOW_GENRES:
        # Split genre lists into individual genres, keeping only new ones
        genres = []
        for genre_list in data["Genres"]:
            for genre in genre_list:
                for g in genre.split(","):
                    if g not in genres:
                        genres.append(g)

        # Print num of genres
        print("Found " + str(len(genres)) + " unique genres.") if VERBOSE else None

        # Create nodes for genres
        for genre in genres:
            # Get category from category-genre mapping
            category = genre_to_category(genre)
            nodes.append({"id": genre, "type": "genre", "label": genre, "color": category_colors[categories.index(category)].hex, "size": 5, "bipartite": 0})

        if SHOW_SONGS:
            # Create edges between tracks and genres
            for spotify_id in spotify_ids:
                track_data = data[data["Spotify ID"] == spotify_id]
                genre = track_data["Category"].iloc[0]
                category = genre_to_category(genre)
                edges.append({"source": spotify_id, "target": genre, "color": category_colors[categories.index(category)].hex})

        # Create edges for genre > user connections
        if SHOW_GENRE_USERS:
            for user in users:
                user_data = data[data["user"] == user]
                user_genres = []
                for genre_list in user_data["Genres"]:
                    for genre in genre_list:
                        for g in genre.split(","):
                            if g not in user_genres:
                                user_genres.append(g)

                for genre in user_genres:
                    category = genre_to_category(genre)
                    edges.append({"source": user, "target": genre, "color": category_colors[categories.index(category)].hex})

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
        print(f"Error loading data: {repr(e)}")
        return

    try:
        print("\nCleaning data...")
        cleaned_data = clean_data(data)
        print("Data cleaned successfully.")
    except Exception as e:
        print(f"Error cleaning data: {repr(e)}")
        return

    try:
        print("\nPreparing nodes and edges...")
        nodes, edges = create_nodes_and_edges(cleaned_data)
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
        print(f"An error occurred: {repr(e)}")
        sys.exit(1)

# End of file