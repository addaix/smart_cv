"Streamlit interface for the CV processing"

# streamlit interface
import streamlit as st
from smart_cv import cv_content, fill_template, mall, dag_pipeline
from smart_cv.util import extension_based_decoding
from meshed import DAG
from smart_cv.base import mall


print("Avaible CVs in the app: ",list(mall.cvs))
funcs = [cv_content, fill_template]


st.title("DT generation app")
st.write("This app is used to process your CVs and generate the corresponding DTs.")

# upload CVs
st.write("Upload the CVs")
uploaded_file = st.file_uploader("Choose a file", accept_multiple_files=False, type=["pdf", "docx"])
# parameters for the CVs processing
# help information
st.sidebar.write("Set the parameters for the DT processing")
api_key = st.sidebar.text_input("API key")
dag = dag_pipeline["_mk_parser":"fill_template"](api_key=api_key)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0)
chunk_overlap = st.sidebar.slider("Chunk overlap", 0, 300, 50)

if uploaded_file is not None:
    bytes_data = uploaded_file.read()
    filename = uploaded_file.name
    name_of_cv = filename.split(".")[0]
    text = extension_based_decoding(filename, bytes_data)

    # drop down list for the language
    language = st.selectbox("Choose the language: 'automatique' write the DT in the same language than the CV", ["automatique","french", "english"])
    print(temperature, chunk_overlap)
    # process the CVs
    if st.button("Process CVs"):
        st.write("Processing...")
        filepath = dag(text, language=language, cv_name=name_of_cv, temperature=temperature, chunk_overlap=chunk_overlap)
        print("The filled CV is saved at: ", filepath)
        # dowload a file with given filepath
        
        save_name = name_of_cv + "_filled.docx"
        st.write(f"Download the filled CV: {save_name}")
        st.download_button(label="Download", 
                           data=open(filepath, 'rb').read(),
                           file_name=save_name, 
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
