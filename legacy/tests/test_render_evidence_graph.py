#!/usr/bin/env python3
"""
Test script to render evidence graph from example JSON data.
"""

import json
import os
import sys
import tempfile
import warnings
from typing import Dict, Any

# Add the parent directory to the path to allow direct imports
sys.path.insert(0, '/Users/zifeng/Documents/github/BioDSA-dev')


def render_evidence_graph(evidence_graph_data: Dict[str, Any], output_path: str) -> bool:
    """
    Render the evidence graph to an image file.
    
    Args:
        evidence_graph_data: Dictionary containing entities and relations
        output_path: Path where the graph image should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not evidence_graph_data or not evidence_graph_data.get('entities'):
        return False
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError:
        warnings.warn(
            "matplotlib and networkx are required for graph visualization. "
            "Install them with: pip install matplotlib networkx"
        )
        return False
    
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes with attributes
        entities = evidence_graph_data.get('entities', [])
        for entity in entities:
            entity_name = entity.get('name', 'Unknown')
            entity_type = entity.get('entityType', 'UNKNOWN')
            observations = entity.get('observations', [])
            
            # Add node with type as attribute
            G.add_node(entity_name, 
                      entity_type=entity_type,
                      observations=observations)
        
        # Add edges
        relations = evidence_graph_data.get('relations', [])
        for relation in relations:
            from_node = relation.get('from', '')
            to_node = relation.get('to', '')
            rel_type = relation.get('relationType', 'RELATED')
            
            if from_node and to_node:
                G.add_edge(from_node, to_node, relation=rel_type)
        
        # Create figure with large size for readability
        fig, ax = plt.subplots(figsize=(20, 16))
        
        # Define colors for different entity types
        entity_type_colors = {
            'PAPER': '#FFB6C1',        # Light pink
            'CHEMICAL': '#87CEEB',      # Sky blue
            'CELLLINE': '#98FB98',      # Pale green
            'GENE': '#FFD700',          # Gold
            'ResearchIntent': '#DDA0DD', # Plum
            'RESEARCH_QUESTION': '#DDA0DD', # Plum
            'Chemical': '#87CEEB',      # Sky blue
            'CellLine': '#98FB98',      # Pale green
            'Gene': '#FFD700',          # Gold
            'Paper': '#FFB6C1',         # Light pink
        }
        
        # Assign colors to nodes
        node_colors = []
        for node in G.nodes():
            entity_type = G.nodes[node].get('entity_type', 'UNKNOWN')
            node_colors.append(entity_type_colors.get(entity_type, '#D3D3D3'))
        
        # Use spring layout for better visualization
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, 
                             node_color=node_colors,
                             node_size=3000,
                             alpha=0.9,
                             ax=ax)
        
        # Draw edges with arrows
        nx.draw_networkx_edges(G, pos,
                             edge_color='gray',
                             alpha=0.5,
                             arrows=True,
                             arrowsize=15,
                             arrowstyle='->',
                             width=1.5,
                             ax=ax)
        
        # Draw labels with smaller font for readability
        labels = {}
        for node in G.nodes():
            # Truncate long names
            label = node
            if len(label) > 30:
                label = label[:27] + '...'
            labels[node] = label
        
        nx.draw_networkx_labels(G, pos, labels,
                              font_size=8,
                              font_weight='bold',
                              ax=ax)
        
        # Add edge labels (relation types)
        edge_labels = nx.get_edge_attributes(G, 'relation')
        # Truncate edge labels
        edge_labels = {k: v[:15] + '...' if len(v) > 15 else v 
                      for k, v in edge_labels.items()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels,
                                   font_size=6,
                                   font_color='darkblue',
                                   ax=ax)
        
        # Add legend for entity types
        from matplotlib.patches import Patch
        legend_elements = []
        used_types = set(G.nodes[node].get('entity_type', 'UNKNOWN') for node in G.nodes())
        for entity_type in sorted(used_types):
            color = entity_type_colors.get(entity_type, '#D3D3D3')
            legend_elements.append(Patch(facecolor=color, label=entity_type))
        
        ax.legend(handles=legend_elements, loc='upper left', 
                 fontsize=10, framealpha=0.9)
        
        # Add title and statistics
        num_entities = len(entities)
        num_relations = len(relations)
        ax.set_title(f'Evidence Graph\n({num_entities} entities, {num_relations} relations)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.axis('off')
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        
        return True
        
    except Exception as e:
        warnings.warn(f"Failed to render evidence graph: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # Load the example evidence graph data
    json_path = "/Users/zifeng/Documents/github/example_evidence_graph_data.json"
    
    print(f"Loading evidence graph data from: {json_path}")
    with open(json_path, 'r') as f:
        evidence_graph_data = json.load(f)
    
    print(f"Loaded {len(evidence_graph_data.get('entities', []))} entities")
    print(f"Loaded {len(evidence_graph_data.get('relations', []))} relations")
    
    # Render the graph to a PNG file
    output_path = "/Users/zifeng/Documents/github/test_evidence_graph.png"
    print(f"\nRendering evidence graph to: {output_path}")
    
    success = render_evidence_graph(evidence_graph_data, output_path)
    
    if success:
        print(f"✓ Successfully rendered evidence graph!")
        print(f"✓ Graph saved to: {output_path}")
        print(f"\nGraph statistics:")
        print(f"  - Entities: {len(evidence_graph_data.get('entities', []))}")
        print(f"  - Relations: {len(evidence_graph_data.get('relations', []))}")
        
        # Count entity types
        entity_types = {}
        for entity in evidence_graph_data.get('entities', []):
            entity_type = entity.get('entityType', 'UNKNOWN')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        print(f"\n  Entity type breakdown:")
        for entity_type, count in sorted(entity_types.items()):
            print(f"    - {entity_type}: {count}")
        
        # Count relation types
        relation_types = {}
        for relation in evidence_graph_data.get('relations', []):
            rel_type = relation.get('relationType', 'UNKNOWN')
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        print(f"\n  Relation type breakdown:")
        for rel_type, count in sorted(relation_types.items()):
            print(f"    - {rel_type}: {count}")
    else:
        print("✗ Failed to render evidence graph")
        print("Make sure matplotlib and networkx are installed:")
        print("  pip install matplotlib networkx")


if __name__ == "__main__":
    main()
