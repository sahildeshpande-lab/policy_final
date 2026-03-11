from langchain_huggingface import HuggingFaceEmbeddings
import os

def get_embeddings():
    cache_dir = "./models_cache"

    os.makedirs(cache_dir, exist_ok=True)
    os.environ["HF_HOME"] = cache_dir

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_folder=cache_dir
    )

# from langchain_huggingface import HuggingFaceEmbeddings
# import os

# def get_embeddings():
#     cache_dir = "./models_cache"

#     os.makedirs(cache_dir, exist_ok=True)
#     os.environ["HF_HOME"] = cache_dir

#     return HuggingFaceEmbeddings(
#         model_name="sentence-transformers/all-MiniLM-L6-v2",
#         cache_folder=cache_dir
#     )
