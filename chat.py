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

def process_pdf_file(pdf_file : cl.types.AskFileResponse)->list[Document]:
    # Load documents with PDFReader
    reader = ... # TODO 1
    docs = ... # TODO 1

    return docs

def create_vector_store(docs: list[Document]) -> VectorStoreIndex:
    # Select embedding model
    embed_model = ... # TODO 2

    # Setup text splitter
    splitter = ... # TODO 3

    # Create Vector index from pdf documents
    index = ... # TODO 4

    return index

def pdf_file_vector_store(pdf_file):
    return create_vector_store(process_pdf_file(pdf_file))

def load_llm():
    return ... # TODO 5

def get_query_engine(pdf_file):
    # Create own prompt with context
    qa_prompt = ... # TODO 6

    # Call functions to load vector store and llm
    index = ... # TODO 7
    llm = ... # TODO 7

    # Callback for the chainlit events
    ... # TODO 8

    # Create query engine
    query_engine = ... # TODO 9

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
    query_engine = ... # TODO 10

    # Notify the user that everything is loaded.
    message.content = f"`{pdf_file.name}` file has been processed. Feel free to ask any questions about it !"
    await message.update()

    # Saves the qa_chain into the user session.
    ... # TODO 11

@cl.on_message
async def main(message):
    # Retrieve the qa_chain saved in the session
    ... # TODO 12

    # Run the question to the query engine and update the answer in chainlit
    ... # TODO 13
