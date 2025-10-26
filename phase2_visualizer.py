"""
PHASE 2 VISUALIZER MODULE
3D Molecules (Three.js), Reaction Animations, Concept Maps

Author: @aryansmilezzz
Admin ID: 6298922725
Phase: 2
"""
import asyncio
import re
import io
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 3D MOLECULE GENERATOR (Three.js - No RDKit!)
# ============================================================================

def generate_3d_molecule_html(formula):
    """
    Generate interactive 3D molecule using Three.js
    Input: Chemical formula (e.g., "CH3CH2OH", "C6H6")
    Output: HTML file with interactive 3D visualization
    """
    
    # Parse formula to get atom counts
    atoms = parse_chemical_formula(formula)
    
    # Generate 3D coordinates (simple heuristic placement)
    coordinates = generate_molecule_coordinates(atoms, formula)
    
    # Create Three.js HTML
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>3D Molecule: {formula}</title>
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 10px;
            z-index: 100;
        }}
        #info h2 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        #info p {{
            margin: 5px 0;
            font-size: 14px;
        }}
        #controls {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div id="info">
        <h2>🧬 {formula}</h2>
        <p>Interactive 3D Molecule</p>
        <p>Atoms: {len(atoms)}</p>
    </div>
    
    <div id="controls">
        🖱️ Drag to rotate | 🔄 Scroll to zoom
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        // Scene setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setClearColor(0x000000, 0);
        document.body.appendChild(renderer.domElement);
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 5, 5);
        scene.add(directionalLight);
        
        // Atom colors (CPK coloring)
        const atomColors = {{
            'C': 0x909090,  // Carbon - gray
            'H': 0xFFFFFF,  // Hydrogen - white
            'O': 0xFF0000,  // Oxygen - red
            'N': 0x0000FF,  // Nitrogen - blue
            'S': 0xFFFF00,  // Sulfur - yellow
            'Cl': 0x00FF00, // Chlorine - green
            'Br': 0xA52A2A, // Bromine - brown
            'I': 0x9400D3   // Iodine - purple
        }};
        
        const atomSizes = {{
            'C': 0.7, 'H': 0.3, 'O': 0.6, 'N': 0.65, 
            'S': 0.8, 'Cl': 0.75, 'Br': 0.85, 'I': 0.95
        }};
        
        // Create atoms
        const atoms = {coordinates};
        
        atoms.forEach(atom => {{
            const geometry = new THREE.SphereGeometry(atomSizes[atom.element] || 0.5, 32, 32);
            const material = new THREE.MeshPhongMaterial({{
                color: atomColors[atom.element] || 0xCCCCCC,
                shininess: 100
            }});
            const sphere = new THREE.Mesh(geometry, material);
            sphere.position.set(atom.x, atom.y, atom.z);
            scene.add(sphere);
            
            // Add bonds (simple cylinder between close atoms)
            atoms.forEach(other => {{
                if (atom !== other) {{
                    const dist = Math.sqrt(
                        Math.pow(atom.x - other.x, 2) +
                        Math.pow(atom.y - other.y, 2) +
                        Math.pow(atom.z - other.z, 2)
                    );
                    
                    // If atoms are close enough, draw bond
                    if (dist < 2.0) {{
                        const bondGeometry = new THREE.CylinderGeometry(0.1, 0.1, dist, 8);
                        const bondMaterial = new THREE.MeshPhongMaterial({{ color: 0xAAAAAA }});
                        const bond = new THREE.Mesh(bondGeometry, bondMaterial);
                        
                        // Position and orient cylinder
                        bond.position.set(
                            (atom.x + other.x) / 2,
                            (atom.y + other.y) / 2,
                            (atom.z + other.z) / 2
                        );
                        
                        const direction = new THREE.Vector3(
                            other.x - atom.x,
                            other.y - atom.y,
                            other.z - atom.z
                        ).normalize();
                        
                        bond.quaternion.setFromUnitVectors(
                            new THREE.Vector3(0, 1, 0),
                            direction
                        );
                        
                        scene.add(bond);
                    }}
                }}
            }});
        }});
        
        // Camera position
        camera.position.z = 15;
        
        // Mouse controls
        let isDragging = false;
        let previousMousePosition = {{ x: 0, y: 0 }};
        let rotation = {{ x: 0, y: 0 }};
        
        renderer.domElement.addEventListener('mousedown', (e) => {{
            isDragging = true;
        }});
        
        renderer.domElement.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                const deltaMove = {{
                    x: e.offsetX - previousMousePosition.x,
                    y: e.offsetY - previousMousePosition.y
                }};
                
                rotation.x += deltaMove.y * 0.01;
                rotation.y += deltaMove.x * 0.01;
            }}
            
            previousMousePosition = {{
                x: e.offsetX,
                y: e.offsetY
            }};
        }});
        
        renderer.domElement.addEventListener('mouseup', () => {{
            isDragging = false;
        }});
        
        // Zoom with mouse wheel
        renderer.domElement.addEventListener('wheel', (e) => {{
            e.preventDefault();
            camera.position.z += e.deltaY * 0.01;
            camera.position.z = Math.max(5, Math.min(30, camera.position.z));
        }});
        
        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            
            // Auto-rotate slowly
            if (!isDragging) {{
                rotation.y += 0.002;
            }}
            
            scene.rotation.x = rotation.x;
            scene.rotation.y = rotation.y;
            
            renderer.render(scene, camera);
        }}
        
        animate();
        
        // Handle window resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>
"""
    
    return html_content

def parse_chemical_formula(formula):
    """
    Parse chemical formula to extract atoms
    Example: "CH3CH2OH" -> [C, C, H, H, H, H, H, O, H]
    """
    # Clean formula
    formula = formula.replace('_', '').replace('^', '').replace(' ', '')
    
    # Extract atoms with regex
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, formula)
    
    atoms = []
    for element, count in matches:
        count = int(count) if count else 1
        atoms.extend([element] * count)
    
    return atoms

def generate_molecule_coordinates(atoms, formula):
    """
    Generate 3D coordinates for atoms using simple heuristics
    This is a basic implementation - not chemically perfect but visual!
    """
    coordinates = []
    
    # Simple linear chain for organic molecules
    if 'C' in atoms:
        carbon_count = atoms.count('C')
        hydrogen_count = atoms.count('H')
        oxygen_count = atoms.count('O')
        
        # Place carbons in a chain
        carbon_positions = []
        for i in range(carbon_count):
            # Zigzag pattern
            x = i * 1.5
            y = 0.5 if i % 2 == 0 else -0.5
            z = 0
            carbon_positions.append({'element': 'C', 'x': x, 'y': y, 'z': z})
            coordinates.append({'element': 'C', 'x': x, 'y': y, 'z': z})
        
        # Place hydrogens around carbons
        h_index = 0
        for i, carbon in enumerate(carbon_positions):
            # Each carbon typically has 2-4 hydrogens
            h_per_carbon = min(4, hydrogen_count - h_index)
            
            for j in range(h_per_carbon):
                angle = (j / h_per_carbon) * 2 * 3.14159
                h_x = carbon['x'] + 1.0 * (j - h_per_carbon/2) * 0.3
                h_y = carbon['y'] + 0.8 if j % 2 == 0 else carbon['y'] - 0.8
                h_z = 0.5 if j < h_per_carbon/2 else -0.5
                
                coordinates.append({'element': 'H', 'x': h_x, 'y': h_y, 'z': h_z})
                h_index += 1
                if h_index >= hydrogen_count:
                    break
            
            if h_index >= hydrogen_count:
                break
        
        # Place oxygen/other atoms
        for i in range(oxygen_count):
            o_x = carbon_positions[-1]['x'] + 1.5
            o_y = carbon_positions[-1]['y']
            o_z = 0
            coordinates.append({'element': 'O', 'x': o_x, 'y': o_y, 'z': o_z})
    
    else:
        # Simple placement for other molecules
        for i, atom in enumerate(atoms):
            coordinates.append({
                'element': atom,
                'x': i * 1.5,
                'y': 0,
                'z': 0
            })
    
    return coordinates

# ============================================================================
# CONCEPT MAP GENERATOR
# ============================================================================

def generate_concept_map_html(topic, related_concepts=None):
    """
    Generate visual concept map using D3.js
    Shows relationships between chemistry concepts
    """
    
    if related_concepts is None:
        related_concepts = get_default_concepts(topic)
    
    # Convert to D3 graph format
    nodes = []
    links = []
    
    # Central node
    nodes.append({
        "id": topic,
        "group": 1,
        "size": 30
    })
    
    # Related nodes
    for i, concept in enumerate(related_concepts):
        nodes.append({
            "id": concept['name'],
            "group": concept.get('group', 2),
            "size": 20
        })
        links.append({
            "source": topic,
            "target": concept['name'],
            "value": concept.get('strength', 1)
        })
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Concept Map: {topic}</title>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            overflow: hidden;
        }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            color: white;
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 10px;
            z-index: 100;
        }}
        svg {{
            width: 100vw;
            height: 100vh;
        }}
        .links line {{
            stroke: #999;
            stroke-opacity: 0.6;
        }}
        .nodes circle {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
        }}
        .nodes text {{
            font-size: 12px;
            fill: white;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div id="info">
        <h2>🗺️ {topic}</h2>
        <p>Interactive Concept Map</p>
        <p>🖱️ Drag nodes to explore</p>
    </div>
    
    <svg></svg>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <script>
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        const svg = d3.select("svg");
        
        const graph = {{
            nodes: {nodes},
            links: {links}
        }};
        
        // Color scale
        const color = d3.scaleOrdinal(d3.schemeCategory10);
        
        // Force simulation
        const simulation = d3.forceSimulation(graph.nodes)
            .force("link", d3.forceLink(graph.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(50));
        
        // Links
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(graph.links)
            .enter().append("line")
            .attr("stroke-width", d => Math.sqrt(d.value) * 2);
        
        // Nodes
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("g")
            .data(graph.nodes)
            .enter().append("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        node.append("circle")
            .attr("r", d => d.size)
            .attr("fill", d => color(d.group));
        
        node.append("text")
            .text(d => d.id)
            .attr("x", d => d.size + 5)
            .attr("y", 5);
        
        // Update positions
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});
        
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
    </script>
</body>
</html>
"""
    
    return html

def get_default_concepts(topic):
    """Get default related concepts for a topic"""
    
    concept_map = {
        "SN1": [
            {"name": "Carbocation", "group": 2, "strength": 3},
            {"name": "Racemization", "group": 2, "strength": 2},
            {"name": "Rate = k[RX]", "group": 3, "strength": 2},
            {"name": "NGP Boost", "group": 4, "strength": 3},
            {"name": "Stability", "group": 2, "strength": 2},
            {"name": "Tertiary > Secondary", "group": 2, "strength": 1}
        ],
        "SN2": [
            {"name": "Backside Attack", "group": 2, "strength": 3},
            {"name": "Inversion", "group": 2, "strength": 3},
            {"name": "Rate = k[Nu][RX]", "group": 3, "strength": 2},
            {"name": "Primary > Secondary", "group": 2, "strength": 2},
            {"name": "180° Attack", "group": 2, "strength": 2}
        ],
        "NGP": [
            {"name": "π-participation", "group": 2, "strength": 3},
            {"name": "n-participation", "group": 2, "strength": 3},
            {"name": "10^6-10^14 boost", "group": 4, "strength": 3},
            {"name": "C=C within 2-3 atoms", "group": 2, "strength": 2},
            {"name": "Orbital overlap", "group": 3, "strength": 2}
        ]
    }
    
    return concept_map.get(topic.upper(), [
        {"name": "Related Concept 1", "group": 2, "strength": 2},
        {"name": "Related Concept 2", "group": 2, "strength": 2}
    ])

# ============================================================================
# REACTION ANIMATOR (Matplotlib GIF frames)
# ============================================================================

def generate_reaction_animation_description(reaction_text):
    """
    Generate a description of reaction animation steps
    (Actual matplotlib animation would be too heavy - we describe instead)
    """
    
    steps = [
        "🎬 Frame 1: Reactants approaching",
        "🎬 Frame 2: Bond breaking begins",
        "🎬 Frame 3: Intermediate formation",
        "🎬 Frame 4: New bond forming",
        "🎬 Frame 5: Products formed"
    ]
    
    description = f"""
📹 *REACTION ANIMATION PREVIEW*

Reaction: {reaction_text}

*Animation Steps:*
{chr(10).join(steps)}

*Key Features:*
• Electron flow arrows
• Bond breaking/forming
• Orbital interactions
• Energy diagram overlay

_Full animation requires video rendering_
_This preview shows the mechanism steps_
"""
    
    return description

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def visualize_molecule_command(update, context, formula):
    """Generate and send 3D molecule HTML"""
    try:
        html_content = generate_3d_molecule_html(formula)
        
        # Save to BytesIO
        html_file = BytesIO(html_content.encode('utf-8'))
        html_file.name = f"molecule_{formula}.html"
        
        await update.message.reply_document(
            document=html_file,
            filename=f"3D_{formula}.html",
            caption=f"🧬 *3D Molecule: {formula}*\n\nOpen in browser for interactive view!\n_Drag to rotate, scroll to zoom_",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"3D molecule error: {e}")
        await update.message.reply_text(f"❌ Error generating 3D molecule: {str(e)[:100]}")

async def visualize_concept_map_command(update, context, topic):
    """Generate and send concept map HTML"""
    try:
        html_content = generate_concept_map_html(topic)
        
        html_file = BytesIO(html_content.encode('utf-8'))
        html_file.name = f"concept_map_{topic}.html"
        
        await update.message.reply_document(
            document=html_file,
            filename=f"ConceptMap_{topic}.html",
            caption=f"🗺️ *Concept Map: {topic}*\n\nInteractive mind map!\n_Drag nodes to explore connections_",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Concept map error: {e}")
        await update.message.reply_text(f"❌ Error generating concept map: {str(e)[:100]}")
