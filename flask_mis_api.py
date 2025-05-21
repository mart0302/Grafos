# Importamos las librerías necesarias
from flask import Flask, request, jsonify  # Flask para crear la API web
import networkx as nx                     # NetworkX para trabajar con grafos
from flask_cors import CORS               # CORS permite acceso desde el frontend aunque esté en otro dominio

# Inicializamos la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitamos CORS para permitir que el frontend pueda comunicarse con esta API

# Función principal para calcular el MIS en grafos outerplanar
def compute_mis_outerplanar(G):

    # Subfunción optimizada para grafos que son árboles
    def compute_mis_tree(G):
        if len(G.nodes()) == 0:
            return []

        root = next(iter(G.nodes()))
        parent = {root: None}
        visited = set()
        stack = [root]

        # DFS para construir relaciones padre-hijo
        while stack:
            u = stack.pop()
            if u not in visited:
                visited.add(u)
                for v in G.neighbors(u):
                    if v not in visited and v != parent[u]:
                        parent[v] = u
                        stack.append(v)

        post_order = list(nx.dfs_postorder_nodes(G, root))
        dp_include = {}  # Valor al incluir el nodo
        dp_exclude = {}  # Valor al excluir el nodo

        # Programación dinámica desde hojas hacia la raíz
        for u in post_order:
            children = [v for v in G.neighbors(u) if v != parent[u]]
            include_u = 1 + sum(dp_exclude.get(v, 0) for v in children)
            exclude_u = sum(max(dp_include.get(v, 0), dp_exclude.get(v, 0)) for v in children)
            dp_include[u] = include_u
            dp_exclude[u] = exclude_u

        mis = []
        stack = [(root, dp_include[root] > dp_exclude[root])]

        # Reconstrucción del conjunto MIS
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

    # Caso base: grafo vacío
    if len(G.nodes()) == 0:
        return []

    # Si es un árbol, usamos la función optimizada
    if nx.is_tree(G):
        return compute_mis_tree(G)

    # Caso general con ciclo: dividir y conquistar
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


# Endpoint para recibir un grafo y calcular su MIS si es outerplanar
@app.route('/compute_mis', methods=['POST'])
def compute_mis():
    data = request.get_json()  # Recibimos datos en formato JSON
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # Validamos que sea un grafo outerplanar
    is_planar, embedding = nx.check_planarity(G)
    if not is_planar or len(embedding.faces()) > 1:
        return jsonify({
            'error': 'El grafo no es outerplanar. El algoritmo solo puede aplicarse a grafos outerplanar.'
        }), 400  # Devolvemos código de error 400 (Bad Request)

    # Calculamos el MIS si pasa la validación
    mis = compute_mis_outerplanar(G)
    return jsonify({'mis': mis})


# Ejecutamos el servidor Flask si se ejecuta directamente este archivo
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # El servidor escucha en el puerto 10000
