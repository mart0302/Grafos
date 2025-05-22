from flask import Flask, request, jsonify
import networkx as nx
from flask_cors import CORS
import itertools

app = Flask(__name__)
CORS(app)

def is_outerplanar(G):
    """
    Verifica si un grafo es outerplanar usando múltiples heurísticas.
    Devuelve True si es outerplanar o si no se puede determinar con certeza.
    """
    # Casos triviales
    if len(G.nodes()) <= 2:
        return True
        
    # Los árboles son outerplanar
    if nx.is_tree(G):
        return True
        
    # Grafos no conexos: todos los componentes deben ser outerplanar
    if not nx.is_connected(G):
        return all(is_outerplanar(G.subgraph(c)) for c in nx.connected_components(G))
    
    # Debe ser planar primero
    if not nx.is_planar(G):
        return False
    
    # Verificación de K4 y K2,3 como subgrafos menores
    def has_K4():
        for nodes in itertools.combinations(G.nodes(), 4):
            subgraph = G.subgraph(nodes)
            if len(subgraph.edges()) >= 5:  # K4 tiene 6 aristas
                return True
        return False
        
    def has_K23():
        for pair in itertools.combinations(G.nodes(), 2):
            others = set(G.nodes()) - set(pair)
            for triple in itertools.combinations(others, 3):
                subgraph = G.subgraph(pair + triple)
                edges = [1 for e in subgraph.edges() if e[0] in pair and e[1] in triple]
                if len(edges) >= 6:  # K2,3 completo
                    return True
        return False
    
    if has_K4() or has_K23():
        return False
    
    # Heurística: grafos outerplanar maximales tienen 2n-3 aristas
    max_edges = 2 * len(G.nodes()) - 3
    if len(G.edges()) > max_edges:
        return False
    
    # Otra heurística: debe tener al menos 2 nodos con grado <= 2
    low_degree_nodes = [n for n in G.nodes() if G.degree(n) <= 2]
    if len(low_degree_nodes) < 2:
        return False
    
    # Si pasó todas las verificaciones, asumimos que es outerplanar
    return True

def compute_mis_tree(G):
    """Calcula el MIS para un árbol usando programación dinámica."""
    if len(G.nodes()) == 0:
        return []

    root = next(iter(G.nodes()))
    parent = {root: None}
    visited = set()
    stack = [root]

    # Construir estructura padre-hijo
    while stack:
        u = stack.pop()
        if u not in visited:
            visited.add(u)
            for v in G.neighbors(u):
                if v not in visited and v != parent[u]:
                    parent[v] = u
                    stack.append(v)

    # Procesar en postorden
    post_order = list(nx.dfs_postorder_nodes(G, root))
    dp_include = {}
    dp_exclude = {}

    for u in post_order:
        children = [v for v in G.neighbors(u) if v != parent[u]]
        include_u = 1 + sum(dp_exclude.get(v, 0) for v in children)
        exclude_u = sum(max(dp_include.get(v, 0), dp_exclude.get(v, 0)) for v in children)
        dp_include[u] = include_u
        dp_exclude[u] = exclude_u

    # Reconstruir la solución
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

def compute_mis_outerplanar(G):
    """Calcula el MIS para grafos outerplanar."""
    if len(G.nodes()) == 0:
        return []
        
    # Si es un árbol, usar el algoritmo optimizado
    if nx.is_tree(G):
        return compute_mis_tree(G)
    
    # Encontrar un ciclo base
    try:
        cycle = nx.cycle_basis(G)[0]
    except IndexError:
        return compute_mis_tree(G)
    
    # Seleccionar un nodo del ciclo
    v = cycle[0]
    
    # Caso 1: No incluir v
    G1 = G.copy()
    G1.remove_node(v)
    mis_without_v = compute_mis_outerplanar(G1)
    
    # Caso 2: Incluir v (excluir sus vecinos)
    G2 = G.copy()
    neighbors = list(G.neighbors(v)) + [v]
    G2.remove_nodes_from(neighbors)
    mis_with_v = [v] + compute_mis_outerplanar(G2)
    
    # Devolver el conjunto más grande
    return max(mis_without_v, mis_with_v, key=len)

@app.route('/compute_mis', methods=['POST'])
def compute_mis():
    """Endpoint principal para calcular el MIS."""
    try:
        data = request.get_json()
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        if not nodes:
            return jsonify({'error': 'El grafo no tiene nodos'}), 400
            
        G = nx.Graph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        
        # Verificar outerplanaridad
        is_op = is_outerplanar(G)
        
        # Calcular MIS incluso si no es outerplanar (con advertencia)
        mis = compute_mis_outerplanar(G)
        
        return jsonify({
            'mis': mis,
            'is_outerplanar': is_op,
            'warning': None if is_op else "El grafo puede no ser outerplanar, los resultados podrían no ser óptimos"
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error al procesar el grafo: {str(e)}',
            'is_outerplanar': False
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
