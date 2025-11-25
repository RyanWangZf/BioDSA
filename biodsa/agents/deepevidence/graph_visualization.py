"""
Generate interactive D3.js graph visualizations from evidence graph data.
"""
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


def generate_evidence_graph_html(
    evidence_graph_data: Dict[str, Any],
    output_html_path: str,
    title: str = "Evidence Graph"
) -> bool:
    """
    Generate an interactive D3.js force-directed graph from evidence_graph_data.
    
    Args:
        evidence_graph_data: Dictionary containing 'entities' and 'relations' keys
        output_html_path: Path where the HTML file should be saved
        title: Title for the graph visualization
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not evidence_graph_data or not evidence_graph_data.get('entities'):
        return False
    
    entities = evidence_graph_data.get('entities', [])
    relations = evidence_graph_data.get('relations', [])
    
    # Convert entities to nodes
    nodes = []
    entity_types = set()
    for idx, entity in enumerate(entities):
        entity_name = entity.get('name', f'Entity_{idx}')
        entity_type = entity.get('entityType', 'UNKNOWN').lower()
        entity_types.add(entity_type)
        observations = entity.get('observations', [])
        
        # Create label from name (truncate if too long)
        label = entity_name
        if len(label) > 50:
            label = label[:47] + "..."
        
        nodes.append({
            'id': entity_name,
            'label': label,
            'type': entity_type,
            'observations': observations
        })
    
    # Convert relations to links
    links = []
    for relation in relations:
        source = relation.get('source', '')
        target = relation.get('target', '')
        relation_type = relation.get('relationType', 'related')
        
        if source and target:
            links.append({
                'source': source,
                'target': target,
                'relation': relation_type
            })
    
    # Generate color mapping for entity types
    type_colors = _generate_type_colors(list(entity_types))
    
    # Generate HTML
    html_content = _generate_html_template(
        nodes=nodes,
        links=links,
        type_colors=type_colors,
        title=title
    )
    
    # Write to file
    try:
        output_path = Path(output_html_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return True
    except Exception as e:
        print(f"Error writing HTML file: {e}")
        return False


def _generate_type_colors(entity_types: List[str]) -> Dict[str, str]:
    """Generate color mapping for entity types."""
    # Predefined colors for common types
    common_colors = {
        'paper': '#f48fb1',
        'gene': '#ce93d8',
        'disease': '#ffcc80',
        'drug': '#90caf9',
        'chemical': '#90caf9',
        'protein': '#a5d6a7',
        'pathway': '#fff59d',
        'review': '#b0bec5',
        'trial': '#f48fb1',
        'unknown': '#eeeeee'
    }
    
    # Additional pastel colors for other types
    additional_colors = [
        '#ffccbc', '#d1c4e9', '#c5e1a5', '#ffe082', 
        '#bcaaa4', '#b2dfdb', '#f8bbd0', '#dcedc8'
    ]
    
    type_colors = {}
    color_idx = 0
    for entity_type in entity_types:
        if entity_type in common_colors:
            type_colors[entity_type] = common_colors[entity_type]
        else:
            type_colors[entity_type] = additional_colors[color_idx % len(additional_colors)]
            color_idx += 1
    
    return type_colors


def _generate_html_template(
    nodes: List[Dict],
    links: List[Dict],
    type_colors: Dict[str, str],
    title: str
) -> str:
    """Generate the complete HTML template with embedded data."""
    
    nodes_json = json.dumps(nodes, indent=2)
    links_json = json.dumps(links, indent=2)
    
    # Build color switch cases
    color_cases = []
    for type_name, color in type_colors.items():
        color_cases.append(f'      case "{type_name}": return "{color}";')
    color_switch = '\n'.join(color_cases)
    
    # Build legend data
    legend_items = []
    for type_name in sorted(type_colors.keys()):
        legend_items.append({
            'label': type_name.replace('_', ' ').title(),
            'type': type_name
        })
    legend_json = json.dumps(legend_items, indent=2)
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      padding: 0;
      background: #f7f7f7;
    }}
    #toolbar {{
      padding: 10px 16px;
      background: #ffffff;
      border-bottom: 1px solid #ddd;
      display: flex;
      gap: 8px;
      align-items: center;
    }}
    #graph {{
      width: 100vw;
      height: calc(100vh - 50px);
      background: #fafafa;
    }}
    button {{
      padding: 6px 12px;
      border-radius: 4px;
      border: 1px solid #999;
      background: #f0f0f0;
      cursor: pointer;
      font-size: 14px;
    }}
    button:hover {{
      background: #e2e2e2;
    }}
    .node circle {{
      stroke: #333;
      stroke-width: 1.5px;
    }}
    .node text {{
      font-size: 10px;
      pointer-events: none;
    }}
    .node:hover circle {{
      stroke-width: 3px;
    }}
    .link {{
      stroke: #999;
      stroke-width: 1.5px;
      marker-end: url(#arrow);
    }}
    .legend rect {{
      stroke: #333;
      stroke-width: 0.5px;
    }}
    .tooltip {{
      position: absolute;
      text-align: left;
      padding: 12px;
      font-size: 12px;
      background: rgba(0, 0, 0, 0.8);
      color: #fff;
      border-radius: 4px;
      pointer-events: none;
      max-width: 300px;
      line-height: 1.4;
    }}
  </style>
</head>
<body>
<div id="toolbar">
  <button onclick="downloadSVG()">Download SVG</button>
  <button onclick="downloadPNG()">Download PNG</button>
  <span style="font-size:13px;color:#555;">Drag nodes to rearrange • Scroll to zoom • Click nodes for details</span>
</div>
<div id="graph"></div>

<script>
  const nodes = {nodes_json};
  
  const links = {links_json};

  const width = document.getElementById("graph").clientWidth;
  const height = document.getElementById("graph").clientHeight;

  const svg = d3.select("#graph")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  // Define arrow marker
  svg.append("defs").append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 20)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#999");

  const zoomGroup = svg.append("g");

  // Create tooltip
  const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

  const colorByType = (type) => {{
    switch (type) {{
{color_switch}
      default: return "#eeeeee";
    }}
  }};

  // Define simulation first
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(100).strength(0.3))
    .force("charge", d3.forceManyBody().strength(-200))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(30));

  const link = zoomGroup.append("g")
    .attr("class", "links")
    .selectAll("line")
    .data(links)
    .enter()
    .append("line")
    .attr("class", "link");

  const node = zoomGroup.append("g")
    .attr("class", "nodes")
    .selectAll("g")
    .data(nodes)
    .enter()
    .append("g")
    .attr("class", "node")
    .on("mouseover", showTooltip)
    .on("mouseout", hideTooltip)
    .on("click", nodeClicked)
    .call(drag(simulation));

  node.append("circle")
    .attr("r", 12)
    .attr("fill", d => colorByType(d.type));

  node.append("text")
    .attr("text-anchor", "middle")
    .attr("dy", 3)
    .text(d => d.label);

  // Add tick handler after nodes are created
  simulation.on("tick", ticked);

  function ticked() {{
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
  }}

  function showTooltip(event, d) {{
    let content = `<strong>${{d.id}}</strong><br/>Type: ${{d.type}}`;
    if (d.observations && d.observations.length > 0) {{
      content += `<br/><br/><em>Observations:</em><br/>`;
      d.observations.slice(0, 3).forEach(obs => {{
        const truncated = obs.length > 100 ? obs.substring(0, 100) + "..." : obs;
        content += `• ${{truncated}}<br/>`;
      }});
      if (d.observations.length > 3) {{
        content += `<em>...and ${{d.observations.length - 3}} more</em>`;
      }}
    }}
    
    tooltip.transition()
      .duration(200)
      .style("opacity", 0.9);
    tooltip.html(content)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 28) + "px");
  }}

  function hideTooltip() {{
    tooltip.transition()
      .duration(500)
      .style("opacity", 0);
  }}

  function nodeClicked(event, d) {{
    console.log("Node clicked:", d);
    alert(`Entity: ${{d.id}}\\nType: ${{d.type}}\\n\\nObservations:\\n${{d.observations.join('\\n\\n')}}`);
  }}

  function drag(simulation) {{
    function dragstarted(event, d) {{
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }}

    function dragged(event, d) {{
      d.fx = event.x;
      d.fy = event.y;
    }}

    function dragended(event, d) {{
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }}

    return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
  }}

  // Zoom & pan
  svg.call(
    d3.zoom()
      .scaleExtent([0.3, 3])
      .on("zoom", (event) => {{
        zoomGroup.attr("transform", event.transform);
      }})
  );

  // Legend
  const legendData = {legend_json};

  const legend = svg.append("g")
    .attr("class", "legend")
    .attr("transform", "translate(15,40)");

  const legendItem = legend.selectAll("g")
    .data(legendData)
    .enter()
    .append("g")
    .attr("transform", (d, i) => `translate(0, ${{i * 18}})`);

  legendItem.append("rect")
    .attr("width", 12)
    .attr("height", 12)
    .attr("rx", 2)
    .attr("ry", 2)
    .attr("fill", d => colorByType(d.type));

  legendItem.append("text")
    .attr("x", 18)
    .attr("y", 10)
    .attr("font-size", 11)
    .text(d => d.label);

  // Export SVG
  window.downloadSVG = function () {{
    const svgNode = svg.node();
    const serializer = new XMLSerializer();
    let source = serializer.serializeToString(svgNode);

    if (!source.match(/^<svg[^>]+xmlns="http:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) {{
      source = source.replace(
        /^<svg/,
        '<svg xmlns="http://www.w3.org/2000/svg"'
      );
    }}
    if (!source.match(/^<svg[^>]+"http:\\/\\/www\\.w3\\.org\\/1999\\/xlink"/)) {{
      source = source.replace(
        /^<svg/,
        '<svg xmlns:xlink="http://www.w3.org/1999/xlink"'
      );
    }}

    const blob = new Blob([source], {{ type: "image/svg+xml;charset=utf-8" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "evidence_graph.svg";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }};

  // Export PNG
  window.downloadPNG = function () {{
    const svgNode = svg.node();
    const serializer = new XMLSerializer();
    let source = serializer.serializeToString(svgNode);

    if (!source.match(/^<svg[^>]+xmlns="http:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) {{
      source = source.replace(
        /^<svg/,
        '<svg xmlns="http://www.w3.org/2000/svg"'
      );
    }}

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");

    const img = new Image();
    img.onload = function() {{
      ctx.fillStyle = "#fafafa";
      ctx.fillRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0);
      canvas.toBlob(function(blob) {{
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "evidence_graph.png";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }});
    }};
    img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(source)));
  }};
</script>
</body>
</html>'''
    
    return html_template


def render_evidence_graph_to_pdf(
    html_path: str,
    output_pdf_path: str
) -> bool:
    """
    Convert an HTML evidence graph to PDF using playwright.
    
    Args:
        html_path: Path to the HTML file
        output_pdf_path: Path where the PDF should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is required for PDF export. Install with: pip install playwright")
        print("Then run: playwright install chromium")
        return False
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # Load the HTML file
            html_path_abs = Path(html_path).absolute()
            page.goto(f"file://{html_path_abs}")
            
            # Wait for D3 to render
            page.wait_for_timeout(2000)
            
            # Export to PDF
            page.pdf(path=output_pdf_path, format='A3', landscape=True)
            
            browser.close()
            return True
    except Exception as e:
        print(f"Error rendering PDF: {e}")
        return False

