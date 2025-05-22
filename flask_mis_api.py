from flask import Flask, request, jsonify
from flask_cors import CORS
import networkx as nx

app = Flask(__name__)
CORS(app)

# =========================
# FUNCIÓN PARA VALIDAR OUTERPLANAR
# =========================
def is_outerplanar(G):
    try:
        is_planar, embedding = nx.check_planarity(G)
        if not is_planar:
            return False

        # Heurística segura: grafos con pocos nodos y sin demasiadas aristas
        # Son outerplanar si cumplen  m ≤ 2n - 3
        if len(G.edges()) <= (2 * len(G.nodes()) - 3):
            return True

        return False  # Si tiene demasiadas aristas, no es outerplanar
    except Exception as e:
        print("Error validando outerplanaridad:", e)
        return False

# =========================
# ALGORITMO MIS
# =========================
def compute_mis_outerplanar(G):
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
            dp_include[u] = 1 + sum(dp_exclude.get(v, 0) for v in children)
            dp_exclude[u] = sum(max(dp_include.get(v, 0), dp_exclude.get(v, 0)) for v in children)
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
    mis1 = compute_mis_outerplanar(G1)
    G2 = G.copy()
    G2.remove_nodes_from([v] + list(G.neighbors(v)))
    mis2 = [v] + compute_mis_outerplanar(G2)
    return max(mis1, mis2, key=len)

# =========================
# RUTA DE LA API
# =========================
@app.route('/compute_mis', methods=['POST'])
def compute_mis():
    try:
        data = request.get_json()
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])

        G = nx.Graph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)

        if not is_outerplanar(G):
            return jsonify({'error': 'El grafo no es outerplanar'}), 400

        mis = compute_mis_outerplanar(G)
        return jsonify({'mis': mis})
    except Exception as e:
        print("Error general en /compute_mis:", str(e))
        return jsonify({'error': 'Error interno en el servidor'}), 500

# =========================
# INICIO
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
