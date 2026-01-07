import pdfplumber
import networkx as nx
import os
import glob
from mlx_lm import load, generate
import re

# Config
PDF_DIR = "documents"
MODEL_PATH = "models/HyperCLOVAX-SEED-Think-32B-Text-4bit"
OUTPUT_GRAPH = "crime_ontology.gml"

# Load Model
print(f"Loading model from {MODEL_PATH}...")
try:
    model, tokenizer = load(MODEL_PATH)
    print("Model loaded.")
except Exception as e:
    print(f"Failed to load model: {e}")
    exit(1)

def extract_text_from_pdf(pdf_path, max_pages=3):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= max_pages: break
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def extract_triples_with_llm(text_chunk):
    # Specialized prompt for Tuple extraction
    prompt = f"""<|system|>
You are a knowledge graph extractor. Extract 5 key facts from the text as (Subject, Relation, Object) triples.
Use concise Korean entities.
Format:
Subject | Relation | Object

<|user|>
Text:
{text_chunk}

Extract triples:
<|assistant|>
"""
    response = generate(model, tokenizer, prompt=prompt, max_tokens=200, verbose=False)
    
    triples = []
    for line in response.split('\n'):
        if "|" in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                triples.append((parts[0], parts[1], parts[2]))
    return triples

def build_ontology():
    G = nx.DiGraph()
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    all_triples = []
    
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file}...")
        # Adjusted page limits based on file size
        filesize_mb = os.path.getsize(pdf_file) / (1024 * 1024)
        target_pages = 5 # Reduced for speed in demo
        
        print(f"  Extracting up to {target_pages} pages...")
        text = extract_text_from_pdf(pdf_file, max_pages=target_pages)
        
        # Split into manageable chunks (naive splitting)
        chunks = [text[i:i+800] for i in range(0, len(text), 800)]
        
        for i, chunk in enumerate(chunks):
            print(f"  Analyzing chunk {i+1}/{len(chunks)}...")
            triples = extract_triples_with_llm(chunk)
            for s, p, o in triples:
                if s and p and o:
                    print(f"    Found: {s} -> {p} -> {o}")
                    G.add_edge(s, o, relation=p)
                    all_triples.append((s, p, o))

    # Save
    nx.write_gml(G, OUTPUT_GRAPH)
    print(f"Graph saved to {OUTPUT_GRAPH}")
    
    # Analyze Schema
    relations = [d['relation'] for u, v, d in G.edges(data=True)]
    unique_relations = sorted(list(set(relations)))
    
    print("\n=== Ontology Schema (Inferred Relations) ===")
    for r in unique_relations:
        print(f"- {r}")
        
    print(f"\nTotal Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")

if __name__ == "__main__":
    build_ontology()
