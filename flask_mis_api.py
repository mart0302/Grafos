from flask import Flask, request, jsonify
import networkx as nx
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def is_outerplanar(G):
    """Verificación rigurosa de outerplanaridad"""
    if len(G.nodes()) <= 3:
        return True
    if not nx.is_planar(G):
        return False
    if nx.is_tree(G):
        return True
    if not nx.is_connected(G):
        return all(is_outerplanar(G.subgraph(c)) for c in nx.connected_components(G))
    
    # Eliminación de nodos de grado 2
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
    return len(temp_G.nodes()) <= 3

def compute_mis_outerplanar(G):
    if len(G.nodes()) == 0:
        return []
    if nx.is_tree(G):
        return list(nx.maximal_independent_set(G))
    
    cycle = nx.cycle_basis(G)[0]
    node = cycle[0]
    
    # Caso 1: Incluir el nodo
    G_excl = G.copy()
    neighbors = list(G.neighbors(node)) + [node]
    G_excl.remove_nodes_from(neighbors)
    mis_with = [node] + compute_mis_outerplanar(G_excl)
    
    # Caso 2: Excluir el nodo
    G_incl = G.copy()
    G_incl.remove_node(node)
    mis_without = compute_mis_outerplanar(G_incl)
    
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
                'error': 'El grafo no es outerplanar. Verifica que: 1) Sea plano, 2) Todos los nodos estén en la cara exterior, 3) No contenga K₄ o K₂,₃',
                'is_outerplanar': False
            }), 400
        
        return jsonify({
            'mis': compute_mis_outerplanar(G),
            'is_outerplanar': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'is_outerplanar': False
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
