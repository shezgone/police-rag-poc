import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# Font setup for Korean support in matplotlib
# Try to find AppleGothic (standard on macOS) or Malgun Gothic (Windows)
font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"

# Check if file exists, if not try another common one
import os
if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/AppleGothic.ttf"

try:
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font_name)
except Exception as e:
    print(f"Warning: Korean font setting failed. Characters may not render correctly. {e}")

def visualize_graph(gml_file):
    print(f"Loading graph from {gml_file}...")
    G = nx.read_gml(gml_file)
    
    plt.figure(figsize=(15, 12))
    
    # Layout
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
    
    # Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color='lightblue', alpha=0.9)
    
    # Draw Edges
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, edge_color='gray', arrows=True)
    
    # Draw Labels (Entity Names)
    nx.draw_networkx_labels(G, pos, font_family=font_name, font_size=10, font_weight="bold")
    
    # Draw Edge Labels (Relations)
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_family=font_name, font_size=8, label_pos=0.5)
    
    plt.title("Relation Crime Ontology (Automatic Extraction)", fontsize=16)
    plt.axis('off')
    
    output_img = "crime_ontology_viz.png"
    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_img}")
    # plt.show() # Cannot show in headless environment

if __name__ == "__main__":
    visualize_graph("crime_ontology.gml")
