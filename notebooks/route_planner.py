from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from ant_colony import  AntColony

import osmnx as ox
import requests
import json
import networkx as nx
from IPython.display import IFrame
import folium
import numpy as np
import overpy

#OpenStreetMap'ten bölge haritasının çekilmesi ve kaydedilmesi
'''
print("Harita İndiriliyor ve Graf oluşturuluyor...")
G = ox.graph_from_place('Uskudar, Istanbul, Turkey', network_type='drive')
ox.save_graphml(G, filepath='uskudarfull.graphml')
fig, ax = ox.plot_graph(G)

print("kayıt yaapacak.")
print("Graph Saved")
'''
G = ox.load_graphml('uskudarfull.graphml')
print('GrafML Dosyadan Okundu ve Graf Oluşturuldu.')

ox.plot_graph(G,edge_linewidth=1)

overpass_url = "http://overpass-api.de/api/interpreter"

overpass_query = """
[out:json];
area["name"="Üsküdar"]->.a;
(
  node[amenity =cafe]["name"](area.a);
  node[amenity= restaurant]["name"](area.a);
);

out center;
"""

response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()

with open('places.json', 'w') as outfile:
    json.dump(data, outfile)
    print("POI Listesi Dosyaya Kaydedildi")

with open('places.json', 'r') as f:
    data = json.load(f)
    print("POI Listesi Dosyadan Okundu")

# Kullanıcıya gezebileceği turistik, tarihi ve doğal yerler listelenir.
places = []
counter = 0
for element in data['elements']:
    places.append(element);
    print(str(counter) + "-" + element["tags"]["name"])
    counter += 1

print("Lütfen seçimlerinizi virgülle ayırarak yazınız");
selections = input();
selected_indexes = [int(d) for d in selections.split(',')]

user_places = []
for place_index in selected_indexes:
    user_places.append(places[place_index])
    # print(places[place_index]);

m = folium.Map(location=[40.378724, 28.7251163])

nearest_nodes = []
for place in user_places:
    point = (place["lat"],place["lon"])
    print(place["tags"]["name"])
    nearest = ox.distance.get_nearest_node(G, point, method='haversine', return_dist=False)
    nearest_node = G.nodes[nearest]
    nearest_node["name"] = place["tags"]["name"]
    nearest_nodes.append(nearest_node)

# Tespit edilen düğümler arasında en kısa mesafeler bulunarak distance matrix elde edilir.
distance_matrix = []
for source_node in nearest_nodes:
    distance_row = []
    for target_node in nearest_nodes:
        distance = 0;
        if source_node['osmid'] != target_node['osmid']:
            distance = nx.shortest_path_length(G, source_node['osmid'],target_node['osmid'],weight='length', method='dijkstra')
        distance_row.append(distance)
    distance_matrix.append(distance_row)
print(distance_matrix)

def print_solution(manager, routing, assignment):
    """Prints assignment on console."""
    print('Mesafe: {} metre'.format(assignment.ObjectiveValue()))
    index = routing.Start(0)
    plan_output = 'izlenmesi gereken rota:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(manager.IndexToNode(index))
        previous_index = index
        index = assignment.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += ' {}\n'.format(manager.IndexToNode(index))
    print(plan_output)


for i in range(0, len(distance_matrix)):
    for j in range(0, len(distance_matrix)):
        if i == j:
            distance_matrix[i][j] = np.inf


distance_matrix = np.array(distance_matrix)

print(distance_matrix)
ant_colony = AntColony(distance_matrix, 1, 1, 100, 0.95, alpha=1, beta=1)
shortest_path = ant_colony.run()
print ("shorted_path: {}".format(shortest_path))