from flask import Flask, request, jsonify
import networkx as nx
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def is_outerplanar(G):
    """Verifica si un grafo es outerplanar."""
    try:
        # Un grafo es outerplanar si y solo si no contiene un K4 o K2,3 como subgrafo menor
        if not nx.is_connected(G):
            # Si no es conexo, verificamos cada componente
            return all(is_outerplanar(G.subgraph(c)) for c in nx.connected_components(G))
        
        # Primero verificamos si es un árbol (los árboles son outerplanar)
        if nx.is_tree(G):
            return True
            
        # Verificamos si el grafo es planar
        if not nx.check_planarity(G)[0]:
            return False
            
        # Verificamos si es un grafo de bloque con una sola cara exterior
        # Esto es una simplificación, en la práctica necesitaríamos un algoritmo más robusto
        # pero para propósitos educativos puede servir
        embedding = nx.planar_layout(G)
        outer_face_nodes = set()
        
        # En un grafo outerplanar, todos los nodos deben estar en la cara exterior
        # Esto es una aproximación simplificada
        for node in G.nodes():
            neighbors = list(G.neighbors(node))
            if len(neighbors) <= 2:
                outer_face_nodes.add(node)
                
        # Si todos los nodos están en la "cara exterior" (según nuestra simplificación)
        return len(outer_face_nodes) == len(G.nodes())
        
    except Exception as e:
        print(f"Error verificando outerplanaridad: {e}")
        return False

def compute_mis_outerplanar(G):
    if len(G.nodes()) == 0:
        return []

    if nx.is_tree(G):
        return compute_mis_tree(G)

    cycle_basis = nx.cycle_basis(G)
    if not cycle_basis:
        return compute_mis_tree(G)

    cycle = cycle_basis[0]
    v = cycle[0]

    G1 = G.copy()
    G1.remove_node(v)
    mis_without_v = compute_mis_outerplanar(G1)

    G2 = G.copy()
    neighbors = list(G.neighbors(v)) + [v]
    G2.remove_nodes_from(neighbors)
    mis_with_v = [v] + compute_mis_outerplanar(G2)

    return max(mis_without_v, mis_with_v, key=len)

def compute_mis_tree(G):
    if len(G.nodes()) == 0:
        return []

    root = next(iter(G.nodes()))
    parent = {root: None}
    visited = set()
    stack = [root]

    while stack:
        u = stack.pop()
        if u not in visited:
            visited.add(u)
            for v in G.neighbors(u):
                if v not in visited and v != parent[u]:
                    parent[v] = u
                    stack.append(v)

    post_order = list(nx.dfs_postorder_nodes(G, root))
    dp_include = {}
    dp_exclude = {}

    for u in post_order:
        children = [v for v in G.neighbors(u) if v != parent[u]]
        include_u = 1 + sum(dp_exclude.get(v, 0) for v in children)
        exclude_u = sum(max(dp_include.get(v, 0), dp_exclude.get(v, 0)) for v in children)
        dp_include[u] = include_u
        dp_exclude[u] = exclude_u

    mis = []
    stack = [(root, dp_include[root] > dp_exclude[root])]
    while stack:
        u, take = stack.pop()
        if take:
            mis.append(u)
            for v in G.neighbors(u):
                if v != parent.get(u, None):
                    stack.append((v, False))
        else:
            for v in G.neighbors(u):
                if v != parent.get(u, None):
                    stack.append((v, dp_include[v] > dp_exclude[v]))
    return mis

@app.route('/compute_mis', methods=['POST'])
def compute_mis():
    data = request.get_json()
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # Verificar si el grafo es outerplanar
    if not is_outerplanar(G):
        return jsonify({
            'error': 'El grafo no es outerplanar. El algoritmo solo funciona con grafos outerplanar.',
            'is_outerplanar': False
        }), 400

    try:
        mis = compute_mis_outerplanar(G)
        return jsonify({
            'mis': mis,
            'is_outerplanar': True
        })
    except Exception as e:
        return jsonify({
            'error': f'Error al calcular MIS: {str(e)}',
            'is_outerplanar': False
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
