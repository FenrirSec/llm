import sys
import json
import ollama
import chromadb

with open("methodology.json", "r") as f:
    data = json.load(f)
    documents = []
    for phase in data['PenetrationTest']['Phases']:
        doc = f"{phase['Name']}: {phase['Description']} "
        doc += " ".join([f"{tool['Name']}: {tool['Description']}" for tool in phase.get('Tools', [])])
        documents.append(doc)

client = chromadb.Client()
collection = client.create_collection(name="methodology")

for i, doc in enumerate(documents):
    response = ollama.embeddings(model="mxbai-embed-large", prompt=doc)
    embedding = response["embedding"]
    collection.add(
        ids=[str(i)],
        embeddings=[embedding],
        documents=[doc]
    )

while True:
    user_input = input("Hello! How can I help you today?\n>>> ")

    # Fetching appropriate documentation sections
    response = ollama.embeddings(model="mxbai-embed-large", prompt=user_input)
    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=3
    )

    # Compiling documents in a single string
    flat_documents = [item for sublist in results['documents'] for item in sublist]
    context = " ".join([doc.replace('\n', ' ').strip() for doc in flat_documents])
    context = ' '.join(context.split())

    # Asking the LLM for an answer using the context
    prompt = f"Question: {user_input}\nContext: {context}\nAnswer:"
    output = ollama.generate(
        model="llama3",
        prompt=prompt
    )

    print(output['response'])
