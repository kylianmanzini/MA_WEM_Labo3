from pathlib import Path
import os

from llama_index.readers.file import PDFReader
from llama_index.core import Document
import chainlit as cl
from llama_index.core.callbacks import CallbackManager
from llama_index.core import Settings
import anyio

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.core.prompts import PromptTemplate

MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

def process_pdf_file(pdf_file : cl.types.AskFileResponse)->list[Document]:
    # Load documents with PDFReader
    reader = PDFReader()
    docs = reader.load_data(file=Path(pdf_file.path))

    return docs

def create_vector_store(docs: list[Document]) -> VectorStoreIndex:
    # Select embedding model
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Setup text splitter
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=20)

    # Create Vector index from pdf documents
    index = VectorStoreIndex.from_documents(
        docs,
        embed_model=embed_model,
        transformations=[splitter],
    )

    return index

def pdf_file_vector_store(pdf_file):
    return create_vector_store(process_pdf_file(pdf_file))

def load_llm():
    return Ollama(
        model=MODEL_NAME,
        request_timeout=120.0,
    )

def get_query_engine(pdf_file):
    # Create own prompt with context
    qa_prompt = PromptTemplate(
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Answer the question using only the provided context. "
        "If the answer is not in the context, say you don't know.\n"
        "Question: {query_str}\n"
        "Answer: "
    )

    # Call functions to load vector store and llm
    index = pdf_file_vector_store(pdf_file)
    llm = load_llm()

    # Callback for the chainlit events
    Settings.callback_manager = CallbackManager([cl.LlamaIndexCallbackHandler()])

    # Create query engine
    query_engine = index.as_query_engine(
        llm=llm,
        text_qa_template=qa_prompt,
        streaming=True,
    )

    return query_engine


@cl.on_chat_start
async def start():
    files = None

    # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a PDF file to begin!", accept=["application/pdf"], max_files=1, max_size_mb=100,
        ).send()

    pdf_file = files[0]

    # Notify the user that we are loading stuff.
    message = cl.Message(
        content=f"Processing `{pdf_file.name}` file and loading model.."
    )
    await message.send()
    
    # Load asynchronously the query engine
    query_engine = await anyio.to_thread.run_sync(get_query_engine, pdf_file)

    # Notify the user that everything is loaded.
    message.content = f"`{pdf_file.name}` file has been processed. Feel free to ask any questions about it !"
    await message.update()

    # Saves the qa_chain into the user session.
    cl.user_session.set("query_engine", query_engine)

@cl.on_message
async def main(message):
    # Retrieve the qa_chain saved in the session
    query_engine = cl.user_session.get("query_engine")

    # Run the question to the query engine and update the answer in chainlit
    answer = await cl.Message(content="").send()
    response = await anyio.to_thread.run_sync(query_engine.query, message.content)

    if hasattr(response, "response_gen"):
        for token in response.response_gen:
            await answer.stream_token(token)
    else:
        answer.content = str(response)

    await answer.update()
