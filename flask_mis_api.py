from flask import Flask, request, jsonify
import networkx as nx
from flask_cors import CORS

# Inicializamos la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir peticiones desde el frontend (por ejemplo, React, Vue, etc.)

# Esta función calcula el Máximo Conjunto Independiente (MIS) para un grafo outerplanar
def compute_mis_outerplanar(G):
    # Subfunción para calcular el MIS de un árbol usando programación dinámica
    def compute_mis_tree(G):
        if len(G.nodes()) == 0:
            return []

        root = next(iter(G.nodes()))  # Seleccionamos un nodo arbitrario como raíz
        parent = {root: None}         # Diccionario para rastrear el padre de cada nodo
        visited = set()
        stack = [root]

        # Construimos el árbol padre-hijo para usar en programación dinámica
        while stack:
            u = stack.pop()
            if u not in visited:
                visited.add(u)
                for v in G.neighbors(u):
                    if v not in visited and v != parent[u]:
                        parent[v] = u
                        stack.append(v)

        # Obtenemos los nodos en postorden (del fondo a la raíz)
        post_order = list(nx.dfs_postorder_nodes(G, root))
        dp_include = {}  # Si incluimos el nodo u en el MIS
        dp_exclude = {}  # Si no lo incluimos

        # Fase de cálculo DP: para cada nodo calculamos ambos casos
        for u in post_order:
            children = [v for v in G.neighbors(u) if v != parent[u]]
            include_u = 1 + sum(dp_exclude.get(v, 0) for v in children)  # u está en el MIS => hijos no pueden estar
            exclude_u = sum(max(dp_include.get(v, 0), dp_exclude.get(v, 0)) for v in children)  # u no está => hijos pueden o no
            dp_include[u] = include_u
            dp_exclude[u] = exclude_u

        # Reconstruimos la solución óptima usando los diccionarios
        mis = []
        stack = [(root, dp_include[root] > dp_exclude[root])]  # Decidimos si tomamos o no la raíz
        while stack:
            u, take = stack.pop()
            if take:
                mis.append(u)  # Si tomamos el nodo, no tomamos a sus hijos
                for v in G.neighbors(u):
                    if v != parent.get(u, None):
                        stack.append((v, False))
            else:
                for v in G.neighbors(u):
                    if v != parent.get(u, None):
                        stack.append((v, dp_include[v] > dp_exclude[v]))
        return mis

    # Si el grafo está vacío, no hay nodos en el MIS
    if len(G.nodes()) == 0:
        return []

    # Si el grafo es un árbol (sin ciclos), usamos la versión optimizada
    if nx.is_tree(G):
        return compute_mis_tree(G)

    # En caso contrario, buscamos ciclos
    cycle_basis = nx.cycle_basis(G)

    # Si no hay ciclos, también es un árbol
    if not cycle_basis:
        return compute_mis_tree(G)

    # Tomamos un ciclo como base para dividir el problema
    cycle = cycle_basis[0]
    v = cycle[0]  # Seleccionamos un nodo del ciclo

    # Caso 1: no incluimos el nodo v
    G1 = G.copy()
    G1.remove_node(v)
    mis_without_v = compute_mis_outerplanar(G1)

    # Caso 2: incluimos el nodo v, así que quitamos v y sus vecinos
    G2 = G.copy()
    neighbors = list(G.neighbors(v)) + [v]
    G2.remove_nodes_from(neighbors)
    mis_with_v = [v] + compute_mis_outerplanar(G2)

    # Elegimos la solución con más nodos
    return max(mis_without_v, mis_with_v, key=len)

# Ruta de la API donde el frontend envía un grafo y recibe el MIS calculado
@app.route('/compute_mis', methods=['POST'])
def compute_mis():
    data = request.get_json()  # Leemos el JSON enviado desde el cliente
    nodes = data.get('nodes', [])  # Lista de nodos
    edges = data.get('edges', [])  # Lista de aristas

    # Creamos el grafo usando NetworkX
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # Calculamos el MIS usando el algoritmo principal
    mis = compute_mis_outerplanar(G)

    # Devolvemos el resultado como JSON
    return jsonify({'mis': mis})

# Ejecutamos el servidor si este archivo se corre directamente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # El servidor correrá en http://localhost:10000/
