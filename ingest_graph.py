import networkx as nx
import json

# 1. Load your JSON data
with open('data.json', 'r') as f:
    data = json.load(f)

# 2. Initialize the Graph
# We use MultiDiGraph to allow multiple types of connections between the same items
G = nx.MultiDiGraph()

# 3. Ingest Products & create relationships
for product in data['products']:
    p_id = product['id']
    
    # Add the Product Node
    G.add_node(p_id, 
               type="Product", 
               name=product['name'], 
               category=product['category'],
               price=product.get('pricing', {}))

    # Connect Product to Target Personas (The "Who is it for?" edge)
    for persona in product.get('target_persona', []):
        G.add_node(persona, type="Persona")
        G.add_edge(p_id, persona, relationship="TARGETS_AUDIENCE")

    # Connect Product to other Products (The "Cross-sell" edge)
    for related_id in product.get('cross_sell', []):
        G.add_edge(p_id, related_id, relationship="CROSS_SELL_OPPORTUNITY")

# 4. Ingest Masterclasses
for mc in data['masterclasses']:
    mc_id = mc['id']
    G.add_node(mc_id, type="Masterclass", name=mc['name'], instructor=mc.get('instructor'))
    
    for persona in mc.get('target_persona', []):
        G.add_node(persona, type="Persona")
        G.add_edge(mc_id, persona, relationship="TARGETS_AUDIENCE")

# 5. Ingest Intent Routing (The "Search" edge)
for route in data['intent_routing']:
    intent_name = route['user_intent']
    G.add_node(intent_name, type="UserIntent")
    
    for rec_id in route['recommended_products']:
        G.add_edge(intent_name, rec_id, relationship="SOLVES_INTENT")

print(f"Graph Ingested: {G.number_of_nodes()} nodes and {G.number_of_edges()} edges created.")

