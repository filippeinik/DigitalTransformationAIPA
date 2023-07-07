import streamlit as st
from langchain.chains import LLMChain
from os import environ
from langchain.llms import OpenAI
from langchain.chains import LLMChain, SimpleSequentialChain, SequentialChain
from langchain.prompts import PromptTemplate
from prompts import *
from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA

API_KEY = "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"

environ["OPENAI_API_KEY"] = API_KEY


def readPDF(filename):
    doc_reader = PdfReader(f"/Users/filipp.einik/Desktop/Bachelorarbeit/ai_app/content/{filename}")
    # read data from the file and put them into a variable called raw_text
    raw_text = ''
    for i, page in enumerate(doc_reader.pages):
        text = page.extract_text()
        if text:
            raw_text += text
    
    return raw_text

def splitText(raw_text):
    # Splitting up the text into smaller chunks for indexing
    text_splitter = CharacterTextSplitter(        
        separator = "\n",
        chunk_size = 1000,
        chunk_overlap  = 200, #striding over the text
        length_function = len,
    )
    texts = text_splitter.split_text(raw_text)
    return texts


raw_text = readPDF("businessmodels.pdf")
texts = splitText(raw_text)

# Download embeddings from OpenAI
embeddings = OpenAIEmbeddings() # type: ignore
docsearch = FAISS.from_texts(texts, embeddings)
# set up FAISS as a generic retriever 
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":6})

# create the chain to answer questions 
rqa = RetrievalQA.from_chain_type(llm=OpenAI(),  # type: ignore
                                  chain_type="stuff", 
                                  retriever=retriever,
                                  # return_source_documents=True,
                                )
rqa.input_key = "answer"
rqa.output_key = "rqa_response"


template = PromptTemplate(
        input_variables = ["guest_answer"],
        template = dt_find_unmentioned_segments
    )

reg_llm = OpenAI(temperature=0.1) # type: ignore

reg_chain = LLMChain(
    llm = reg_llm,
    prompt = template,
    verbose = True,
    output_key = "llm_response"
)

seq = SequentialChain(
    chains = [
        reg_chain,
        rqa
    ],
    input_variables = ["guest_answer"],
    output_variables = ["rqa_response", "llm_response"],
    verbose = True
)

# Framework
st.title("Digital Transformation Podcast AI")
prompt = st.text_area("Command or Response")

# render response
if st.button('Absenden'):
    if prompt:
        with st.spinner('Generating response...'):
            # response = rqa(prompt, return_only_outputs=True)
            # answer = response['result']
            # response = seq(prompt, return_only_outputs=True)
            response = seq({"guest_answer" : prompt})
            
            st.write(response)

            
    else:
        st.warning('Please enter your prompt')


def showSources(response):
    for i, doc in enumerate(response["source_documents"]):
                with st.expander(f"Quelle: {str(i)}"):
                    st.write(str(doc))


def createTemplateChain():
    template = PromptTemplate(
        input_variables = ["answer"],
        template = "" #dt_find_unspoken_truth_prompt
    )

    # LLMs
    llm = OpenAI(temperature=0.9) # type: ignore

    initial_chain = LLMChain(
        llm=llm,
        prompt = template
    )