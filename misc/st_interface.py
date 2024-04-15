# streamlit interface
import streamlit as st
from smart_cv import cv_content, fill_template, mall
from smart_cv.util import extension_based_decoding
from meshed import DAG
from smart_cv.base import mall
import os


print("Avaible CVs in the app: ",list(mall.cvs))
funcs = [cv_content, fill_template]
dag = DAG(funcs)


st.title("CVs processing")
st.write("This app is used to process your CVs")

# upload CVs
st.write("Upload the CVs")
uploaded_file = st.file_uploader("Choose a file", accept_multiple_files=False, type=["pdf", "docx"])

if uploaded_file is not None:
    bytes_data = uploaded_file.read()
    filename = uploaded_file.name
    name_of_cv = filename.split(".")[0]
    text = extension_based_decoding(filename, bytes_data)

    # drop down list for the language
    language = st.selectbox("Choose the language", ["french", "english"])

    # process the CVs
    if st.button("Process CVs"):
        st.write("Processing...")
        filepath = dag(text, language=language, cv_name=name_of_cv)
        print("The filled CV is saved at: ", filepath)
        # dowload a file with given filepath
        
        save_name = name_of_cv + "_filled.docx"
        st.write(f"Download the filled CV: {save_name}")
        st.download_button(label="Download", 
                           data=mall.filled[name_of_cv + "_filled.docx"],
                           file_name=save_name, 
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        # remove the file
        mall.filled.pop(filename)




