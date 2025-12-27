import networkx as nx
from typing import List, Dict, Tuple
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """Build knowledge graphs from entities and relationships"""
    
    def __init__(self):
        self.graph = None
    
    async def build_graph(self, entities: List[Dict], relationships: List[Dict] = None) -> Dict:
        """
        Build knowledge graph from entities and relationships
        
        Args:
            entities: List of entity dicts with 'text' and 'label'
            relationships: List of relationship dicts with 'subject', 'relation', 'object'
        
        Returns:
            Graph data in format suitable for visualization
        """
        try:
            # Create directed graph
            G = nx.DiGraph()
            
            # Add entity nodes
            entity_types = defaultdict(list)
            for entity in entities:
                node_id = entity['text']
                node_type = entity['label']
                
                G.add_node(
                    node_id,
                    type=node_type,
                    label=entity['text']
                )
                entity_types[node_type].append(node_id)
            
            # Add relationship edges
            if relationships:
                for rel in relationships:
                    if rel['subject'] in G.nodes and rel['object'] in G.nodes:
                        G.add_edge(
                            rel['subject'],
                            rel['object'],
                            relation=rel.get('relation', 'related_to')
                        )
            
            # If no explicit relationships, create connections between entities of different types
            if not relationships or len(G.edges) == 0:
                await self._create_implicit_connections(G, entities)
            
            # Convert to visualization format
            graph_data = await self._graph_to_dict(G)
            
            # Add statistics
            graph_data['statistics'] = {
                'total_nodes': G.number_of_nodes(),
                'total_edges': G.number_of_edges(),
                'entity_types': {k: len(v) for k, v in entity_types.items()},
                'density': nx.density(G),
                'is_connected': nx.is_weakly_connected(G) if G.number_of_nodes() > 0 else False
            }
            
            self.graph = G
            
            return graph_data
            
        except Exception as e:
            logger.error(f"Knowledge graph building error: {e}")
            return {
                'nodes': [],
                'edges': [],
                'statistics': {},
                'error': str(e)
            }
    
    async def _create_implicit_connections(self, G: nx.DiGraph, entities: List[Dict]):
        """
        Create connections between entities that appear close together
        """
        # Group entities by their position in text (if available)
        # For now, connect entities of different types that might be related
        
        persons = [e['text'] for e in entities if e['label'] == 'PERSON']
        orgs = [e['text'] for e in entities if e['label'] == 'ORG']
        locations = [e['text'] for e in entities if e['label'] == 'GPE']
        
        # Connect persons to organizations
        for person in persons[:5]:  # Limit connections
            for org in orgs[:3]:
                if person in G.nodes and org in G.nodes:
                    G.add_edge(person, org, relation='associated_with')
        
        # Connect organizations to locations
        for org in orgs[:5]:
            for loc in locations[:3]:
                if org in G.nodes and loc in G.nodes:
                    G.add_edge(org, loc, relation='located_in')
    
    async def _graph_to_dict(self, G: nx.DiGraph) -> Dict:
        """Convert NetworkX graph to dictionary format for frontend"""
        nodes = []
        edges = []
        
        # Convert nodes
        for node_id, data in G.nodes(data=True):
            nodes.append({
                'id': node_id,
                'label': data.get('label', node_id),
                'type': data.get('type', 'unknown'),
                'size': G.degree(node_id) + 5  # Size based on connections
            })
        
        # Convert edges
        for source, target, data in G.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'relation': data.get('relation', 'related_to'),
                'label': data.get('relation', '')
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    async def get_central_entities(self, top_n: int = 5) -> List[Dict]:
        """
        Get most central/important entities in the graph
        """
        if not self.graph or self.graph.number_of_nodes() == 0:
            return []
        
        try:
            # Calculate centrality measures
            degree_centrality = nx.degree_centrality(self.graph)
            
            # Sort by centrality
            sorted_entities = sorted(
                degree_centrality.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
            
            central_entities = []
            for entity_id, centrality in sorted_entities:
                node_data = self.graph.nodes[entity_id]
                central_entities.append({
                    'entity': entity_id,
                    'type': node_data.get('type', 'unknown'),
                    'centrality': centrality,
                    'connections': self.graph.degree(entity_id)
                })
            
            return central_entities
            
        except Exception as e:
            logger.error(f"Central entities calculation error: {e}")
            return []
    
    async def find_paths(self, source: str, target: str) -> List[List[str]]:
        """
        Find all paths between two entities
        """
        if not self.graph:
            return []
        
        try:
            if source in self.graph.nodes and target in self.graph.nodes:
                # Find all simple paths (limit to avoid exponential explosion)
                paths = list(nx.all_simple_paths(
                    self.graph,
                    source,
                    target,
                    cutoff=4  # Max path length
                ))
                return paths[:10]  # Return max 10 paths
            return []
            
        except Exception as e:
            logger.error(f"Path finding error: {e}")
            return []
    
    async def get_entity_neighbors(self, entity: str, depth: int = 1) -> Dict:
        """
        Get neighboring entities up to certain depth
        """
        if not self.graph or entity not in self.graph.nodes:
            return {'neighbors': [], 'count': 0}
        
        try:
            # Get neighbors at specified depth
            if depth == 1:
                neighbors = list(self.graph.neighbors(entity))
            else:
                # BFS to get neighbors at depth
                neighbors = set()
                current_level = {entity}
                
                for _ in range(depth):
                    next_level = set()
                    for node in current_level:
                        next_level.update(self.graph.neighbors(node))
                    neighbors.update(next_level)
                    current_level = next_level
                
                neighbors = list(neighbors - {entity})
            
            neighbor_data = []
            for neighbor in neighbors:
                node_data = self.graph.nodes[neighbor]
                neighbor_data.append({
                    'entity': neighbor,
                    'type': node_data.get('type', 'unknown'),
                    'label': node_data.get('label', neighbor)
                })
            
            return {
                'neighbors': neighbor_data,
                'count': len(neighbor_data)
            }
            
        except Exception as e:
            logger.error(f"Neighbor retrieval error: {e}")
            return {'neighbors': [], 'count': 0}
    
    async def export_graph(self, format: str = 'gexf') -> str:
        """
        Export graph to file format (gexf, graphml, etc.)
        """
        if not self.graph:
            return None
        
        try:
            from pathlib import Path
            import tempfile
            
            # Create temp file
            temp_file = Path(tempfile.gettempdir()) / f"knowledge_graph.{format}"
            
            if format == 'gexf':
                nx.write_gexf(self.graph, str(temp_file))
            elif format == 'graphml':
                nx.write_graphml(self.graph, str(temp_file))
            else:
                return None
            
            return str(temp_file)
            
        except Exception as e:
            logger.error(f"Graph export error: {e}")
            return None