import chromadb
chroma_client = chromadb.Client()

collection = chroma_client.create_collection(
    name="ace_user_documents",
    embedding_function=emb_fn,
    metadata = {
        user_id:"abc",
        session_id: "001"
    })


collection.add(
    documents = [
        "this is a test document",
        "this a document about oranges",
    ],
    ids = ["id1" ,"id2"]
)

results = collection.query(
    query_texts = ["this is a document about hawaii"],
    n_results = 2
)

print(results)
