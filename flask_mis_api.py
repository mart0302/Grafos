from flask import Flask, request, jsonify
import networkx as nx
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def is_outerplanar(G):
    """Verificación estricta de outerplanaridad"""
    # Casos base
    if len(G.nodes()) <= 3:
        return True
    if not nx.is_connected(G):
        return all(is_outerplanar(G.subgraph(c)) for c in nx.connected_components(G))
    
    # Eliminamos nodos de grado 2 secuencialmente (propiedad outerplanar)
    temp_G = G.copy()
    changed = True
    while changed and len(temp_G.nodes()) > 3:
        changed = False
        for node in list(temp_G.nodes()):
            if temp_G.degree(node) == 2:
                neighbors = list(temp_G.neighbors(node))
                temp_G.remove_node(node)
                temp_G.add_edge(neighbors[0], neighbors[1])
                changed = True
                break
    
    # Si queda un triángulo o menos, es outerplanar
    return len(temp_G.nodes()) <= 3

def compute_mis_outerplanar(G):
    """Algoritmo específico para outerplanar"""
    if nx.is_tree(G):
        return list(nx.maximal_independent_set(G))
    
    # Selecciona un nodo de grado mínimo en el "exterior"
    node = min(G.nodes(), key=lambda x: G.degree(x))
    neighbors = list(G.neighbors(node))
    
    # Caso 1: Incluir el nodo
    G1 = G.copy()
    G1.remove_nodes_from(neighbors + [node])
    mis_with = [node] + compute_mis_outerplanar(G1)
    
    # Caso 2: Excluir el nodo
    G2 = G.copy()
    G2.remove_node(node)
    mis_without = compute_mis_outerplanar(G2)
    
    return max(mis_with, mis_without, key=len)

@app.route('/compute_mis', methods=['POST'])
def handle_request():
    try:
        data = request.get_json()
        G = nx.Graph()
        G.add_nodes_from(data['nodes'])
        G.add_edges_from(data['edges'])
        
        if not is_outerplanar(G):
            return jsonify({
                'error': 'El grafo no es outerplanar',
                'is_outerplanar': False
            }), 400
        
        return jsonify({
            'mis': compute_mis_outerplanar(G),
            'is_outerplanar': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error: {str(e)}',
            'is_outerplanar': False
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
