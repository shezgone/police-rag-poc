import networkx as nx
from mlx_lm import load, generate
import sys
import os

# Config
GRAPH_FILE = "crime_ontology.gml"
MODEL_PATH = "models/HyperCLOVAX-SEED-Think-32B-Text-4bit"

class SimpleGraphRAG:
    def __init__(self):
        self.graph = None
        self.model = None
        self.tokenizer = None
        self._load_resources()

    def _load_resources(self):
        print("Initializing Simple GraphRAG...")
        
        # 1. Load Graph
        if os.path.exists(GRAPH_FILE):
            print(f"Loading Knowledge Graph from {GRAPH_FILE}...")
            self.graph = nx.read_gml(GRAPH_FILE)
            print(f"Graph loaded: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")
        else:
            print(f"Error: Graph file {GRAPH_FILE} not found. Please run build_ontology.py first.")
            sys.exit(1)

        # 2. Load LLM
        print(f"Loading LLM from {MODEL_PATH}...")
        try:
            self.model, self.tokenizer = load(MODEL_PATH)
            print("LLM loaded successfully.")
        except Exception as e:
            print(f"Error loading LLM: {e}")
            sys.exit(1)

    def retrieve_context(self, query):
        """
        Find relevant nodes in the graph based on the query and return their connections.
        """
        relevant_triples = []
        found_nodes = []
        
        print(f"[GraphX Log] Processing query: '{query}'")
        
        # Fuzzy matching: Ignore spaces and case
        normalized_query = query.replace(" ", "").lower()
        print(f"[GraphX Log] Normalized Search Query: '{normalized_query}'")
        
        for node in self.graph.nodes():
            normalized_node = str(node).replace(" ", "").lower()
            
            # Check for substring match in both directions
            if normalized_node in normalized_query or (len(normalized_query) > 2 and normalized_query in normalized_node):
                 found_nodes.append(node)
                 print(f"[GraphX Log] MATCH NODE (fuzzy): '{node}'")
        
        if not found_nodes:
            print("[GraphX Log] No matching nodes found in the graph.")
            return "No specific knowledge found in the graph."

        # Collect neighborhood
        for node in found_nodes:
            print(f"[GraphX Log] Expanding neighborhood for node: '{node}'")
            
            # Outgoing edges
            for neighbor in self.graph.neighbors(node):
                edge_data = self.graph.get_edge_data(node, neighbor)
                relation = edge_data.get('relation', 'related_to')
                triple = f"{node} -> [{relation}] -> {neighbor}"
                relevant_triples.append(triple)
                print(f"[GraphX Log]   FOUND EDGE: {triple}")
            
            # Incoming edges
            for predecessor in self.graph.predecessors(node):
                edge_data = self.graph.get_edge_data(predecessor, node)
                relation = edge_data.get('relation', 'related_to')
                triple = f"{predecessor} -> [{relation}] -> {node}"
                relevant_triples.append(triple)
                print(f"[GraphX Log]   FOUND EDGE: {triple}")

        # Remove duplicates
        relevant_triples = list(set(relevant_triples))
        
        if not relevant_triples:
            print("[GraphX Log] Nodes found, but no edges connected.")
            return f"Found entities {found_nodes}, but no relationships were recorded."
            
        return "\n".join(relevant_triples)

    def query(self, user_question):
        # 1. Retrieve
        print("\n[Searching Graph...]")
        context = self.retrieve_context(user_question)
        print(f"[Context found]\n{context}\n")

        # 2. Generate
        prompt = f"""<|system|>
당신은 범죄 분석 전문가입니다. 아래 제공된 [문맥]을 바탕으로 사용자의 질문에 자연스러운 한국어로 답변하세요.
'제공된 문맥에 따르면'과 같은 서두는 생략하고, 바로 핵심 내용을 설명하세요.
문맥에 없는 내용은 지어내지 말고 모른다고 답변하세요.

[문맥]:
{context}

<|user|>
질문: {user_question}

<|assistant|>
"""
        print("[Generating Answer...]")
        print(f"--- [LLM Prompt] ---\n{prompt}\n--------------------")
        response = generate(self.model, self.tokenizer, prompt=prompt, max_tokens=512, verbose=False)
        return response

def main():
    rag_system = SimpleGraphRAG()
    
    print("\n" + "="*50)
    print("GraphRAG System Ready. Type 'exit' to quit.")
    print("="*50)

    while True:
        user_input = input("\nquestion > ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            break
        
        if not user_input.strip():
            continue

        answer = rag_system.query(user_input)
        print("\nAnswer:")
        print(answer)

if __name__ == "__main__":
    main()
