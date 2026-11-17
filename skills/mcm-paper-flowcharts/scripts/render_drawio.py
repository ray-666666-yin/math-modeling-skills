"""Generate editable, uncompressed draw.io XML from an explicit JSON layout.

Standard library only. This validates geometry and graph references, not the
scientific meaning, visual text fit, or rendering of the diagram.
"""
import argparse
import html
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

COLORS = {
    "input": "#E8F1E0", "model": "#E5ECF7", "compute": "#FFF3D8",
    "decision": "#F7E2E8", "output": "#FCEBDD", "group": "#F7F8FA",
}
SHAPES = {
    "rounded": "rounded=1;arcSize=12;",
    "rect": "rounded=0;",
    "diamond": "rhombus;",
    "ellipse": "ellipse;",
}


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric.")
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive." if positive else "."))
    return value


def identifier(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string.")
    return value


def label(value):
    if not isinstance(value, str):
        raise ValueError("Labels must be strings.")
    return html.escape(value).replace("\n", "<br>")


def build_document(data):
    if not isinstance(data, dict):
        raise ValueError("Layout must be an object.")
    width = number(data.get("width", 1000), "width", True)
    height = number(data.get("height", 700), "height", True)
    font = data.get("font", "sans-serif")
    if not isinstance(font, str) or not font.strip() or any(c in font for c in ";=\n"):
        raise ValueError("font must be a plain font-family name.")
    nodes, edges = data.get("nodes", []), data.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list) or not nodes:
        raise ValueError("nodes must be a nonempty list and edges must be a list.")
    ids, node_ids = {"0", "1"}, set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("Each node must be an object.")
        node_id = identifier(node.get("id"), "node id")
        if node_id in ids:
            raise ValueError(f"Duplicate or reserved id: {node_id}")
        ids.add(node_id)
        node_ids.add(node_id)
        label(node.get("label", ""))
        role = node.get("role", "model")
        if role not in COLORS:
            raise ValueError(f"Unknown role: {role}")
        shape = node.get("shape", "diamond" if role == "decision" else "rounded")
        if shape not in SHAPES:
            raise ValueError(f"Unknown shape: {shape}")
        x, y = number(node.get("x"), "node x"), number(node.get("y"), "node y")
        w, h = number(node.get("width"), "node width", True), number(node.get("height"), "node height", True)
        number(node.get("fontSize", 18), "fontSize", True)
        if x < 0 or y < 0 or x + w > width or y + h > height:
            raise ValueError(f"Node {node_id} exceeds the page bounds.")

    edge_ids = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError("Each edge must be an object.")
        edge_id = edge.get("id", f"edge-{index + 1}")
        identifier(edge_id, "edge id")
        if edge_id in ids:
            raise ValueError(f"Duplicate or reserved id: {edge_id}")
        ids.add(edge_id)
        edge_ids.append(edge_id)
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids:
            raise ValueError(f"Unknown endpoint in {edge_id}.")
        label(edge.get("label", ""))
        if not isinstance(edge.get("dashed", False), bool):
            raise ValueError("dashed must be boolean.")
        points = edge.get("points", [])
        if not isinstance(points, list):
            raise ValueError("points must be a list.")
        for p in points:
            if not isinstance(p, dict):
                raise ValueError("Each waypoint must be an object.")
            px, py = number(p.get("x"), "point x"), number(p.get("y"), "point y")
            if px < 0 or py < 0 or px > width or py > height:
                raise ValueError(f"Waypoint in {edge_id} exceeds page bounds.")

    mxfile = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", id="page-1", name=str(data.get("title", "Flowchart")))
    model = ET.SubElement(diagram, "mxGraphModel", grid="1", gridSize="10", guides="1",
                          tooltips="1", connect="1", arrows="1", fold="1", page="1",
                          pageScale="1", pageWidth=str(width), pageHeight=str(height))
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    # Group backgrounds are emitted first; all cells remain independently editable.
    ordered_nodes = sorted(nodes, key=lambda n: n.get("role") != "group")
    for node in ordered_nodes:
        role = node.get("role", "model")
        shape = node.get("shape", "diamond" if role == "decision" else "rounded")
        style = (SHAPES[shape] + "whiteSpace=wrap;html=1;"
                 + f"fontFamily={font};fontSize={node.get('fontSize', 18)};"
                 + f"fillColor={COLORS[role]};strokeColor=#59636F;fontColor=#20252D;"
                 + "spacing=8;strokeWidth=1.5;")
        if role == "group":
            style += "dashed=1;verticalAlign=top;align=left;"
        cell = ET.SubElement(root, "mxCell", id=node["id"],
                             value=label(node.get("label", "")), style=style,
                             vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(node["x"]), y=str(node["y"]),
                      width=str(node["width"]), height=str(node["height"]),
                      attrib={"as": "geometry"})
    for edge, edge_id in zip(edges, edge_ids):
        style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;"
                 "endArrow=block;endFill=1;strokeColor=#3C4653;strokeWidth=1.5;"
                 f"fontFamily={font};fontSize=15;labelBackgroundColor=#FFFFFF;")
        if edge.get("dashed", False):
            style += "dashed=1;"
        cell = ET.SubElement(root, "mxCell", id=edge_id, value=label(edge.get("label", "")),
                             style=style, edge="1", parent="1",
                             source=edge["source"], target=edge["target"])
        geometry = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})
        if edge.get("points"):
            array = ET.SubElement(geometry, "Array", attrib={"as": "points"})
            for p in edge["points"]:
                ET.SubElement(array, "mxPoint", x=str(p["x"]), y=str(p["y"]))
    ET.indent(mxfile, space="  ")
    return ET.ElementTree(mxfile)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output paths must differ.")
    if args.output.exists() and not args.overwrite:
        parser.error("Output exists; choose another path or pass --overwrite.")
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    tree = build_document(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(args.output, encoding="utf-8", xml_declaration=True)
    print(json.dumps({"nodes": len(data["nodes"]), "edges": len(data.get("edges", [])),
                      "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

