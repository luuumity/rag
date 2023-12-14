import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))


import os
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
import configparser
import config, vector_store
import streamlit as st
import time

from vector_store.vectorstore import(
    get_retriever
)



# Config Directory
PACKAGE_ROOT = Path(config.__file__).resolve().parent
#print(PACKAGE_ROOT)
CONFIG_FILE_PATH = PACKAGE_ROOT / "rag_config.ini"
#print(CONFIG_FILE_PATH)

rag_config = configparser.ConfigParser()
rag_config.read(CONFIG_FILE_PATH)

input_folder = rag_config['DEFAULT']['input_folder']
output_folder = rag_config['DEFAULT']['output_folder']
chunk_size = int(rag_config['DEFAULT']['chunk_size'])
llm_chat = rag_config['DEFAULT']['llm_chat']


@st.cache_data
def generate_query_response(_agent_chain, query):
    response = _agent_chain({"question": query}, return_only_outputs=False)
    return response

def main_qa():

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY is not set")
    
    chat_model = ChatOpenAI(model_name=llm_chat, temperature=0)
    chat_model.openai_api_key = openai_api_key

    chroma_path = os.path.join(output_folder, rag_config['chroma']['chroma_loc'])
    #use existing vectorDB to query results
    retriever = get_retriever(rag_config['chroma']['collection_name'], chunk_size, chroma_path)
    rag_qa = RetrievalQAWithSourcesChain.from_chain_type(
                    llm=chat_model,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=True
                    )

    st.title("Enterprise QnA chat bot")
    st.markdown("RAG with ChatGPT4 based Q and A application")
    query = ""
    query = st.text_input("Enter the query: ")
    print(query)
    if query != "":
        t3_start = time.time()
        response = generate_query_response(rag_qa, query)
        t3_end = time.time()
        qp_time_taken = t3_end - t3_start
        print("generate_query_response took time to complete -- ", qp_time_taken)
        print(response)
        st.markdown("\nResponse\n\n")
        st.markdown(response["answer"])
        st.markdown("\nSource Documents used:")
        if (response['sources']==''):
            st.markdown("There were no relevant source documents corresponding to this query")
        else:
            if response['sources'].startswith("Output/Text"):
                st.markdown(response['sources'].lstrip(f"Output/Text/Text_").rstrip('.txt'))
            else:
                st.markdown(response['sources'])
        st.markdown("Time taken to complete query processing (secs):")
        st.markdown(qp_time_taken)
    

