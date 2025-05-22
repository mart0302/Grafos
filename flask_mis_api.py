from flask import Flask, request, jsonify
import networkx as nx
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilita CORS para que pueda ser consumido desde el frontend


def compute_mis_outerplanar(G):
    """Calcula el MIS usando un enfoque recursivo sobre grafos outerplanar."""
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


@app.route('/compute_mis', methods=['POST'])
def compute_mis():
    data = request.get_json()
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    mis = compute_mis_outerplanar(G)
    return jsonify({'mis': mis})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
