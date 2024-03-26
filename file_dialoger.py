from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores.chroma import Chroma
from operator import itemgetter
from langchain_community.document_loaders import DirectoryLoader

class File_Dialoger:
    """Class to handle file dialog using RAG and prompts"""
    def __init__(self, document_path=None, api_key=None, retrieve=False, **kwargs):
        self.set_api_key(api_key)
        self.retrieve = retrieve
        self.model = ChatOpenAI(openai_api_key=self._api_key, temperature= kwargs.get("temperature", 0.5))

        if self.retrieve:
            if document_path is not None:
                self.load_document(document_path, **kwargs)
            self.embeddings = OpenAIEmbeddings(openai_api_key=self._api_key, model=kwargs.get("model", 'text-embedding-3-small'))
            # build vector store and retriever
            self.compute_embeddings(**kwargs)

    def set_api_key(self, api_key):
        """Set the OpenAI API key. If not given, it will ask for it."""
        if api_key is not None:
            self._api_key = api_key
        else:
            self._api_key = input("Enter your OpenAI API key: ")
        if self._api_key is None:
            raise ValueError("OpenAI API key is missing")
    
    def load_document(self, document_path, **kwargs):
        """Load the document from the given path. It can be a pdf or a directory containing pdfs."""
        # TODO : Add support for other file types
        if document_path.endswith(".pdf"):
            loader =PyPDFLoader(document_path)
        
        # If it's a directory, load all the pdfs in the directory
        else:
            loader = DirectoryLoader(document_path, glob="**/*.pdf", show_progress=True, loader_cls=PyPDFLoader)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=kwargs.get("chunk_size", 400), chunk_overlap=kwargs.get("chunk_overlap", 100))
        self.documents = self.text_splitter.split_documents(loader.load())
    
    def compute_embeddings(self, **kwargs):
        self.db = Chroma.from_documents(self.documents, self.embeddings)
        self.retriever = self.db.as_retriever(search_kwargs={'k': kwargs.get('k', 5)})

    def build_chain(self, prompt_template=None, context_variable=None, question_variable=None):
        """ Setup a chain with given prompt template and the given context_variable and question_variables
        model : I give you a {context_variable} and you answer: {question_variable}
        Example :
            prompt_template =  I give you a {Law_document} and you answer: {my_question}
            context_variable = "Law_document"
            question_variable = "my_question"
        """
        self.question_variable = question_variable
        self.context_variable = context_variable
        if self.retrieve:
            assert hasattr(self, 'documents'), "Documents are not loaded"
            assert hasattr(self, 'retriever'), "Embeddings are not computed"
            prompt = ChatPromptTemplate.from_template(prompt_template)
            self.chain = (
            {
                context_variable : itemgetter(question_variable) | self.retriever,
                question_variable: itemgetter(question_variable),
            }
            | prompt
            | self.model
            | StrOutputParser()
            )
        else:
            self.chain = (
            self.model
            | StrOutputParser()
            )

    def ask_question(self, question, context=None):
        assert hasattr(self, 'chain'), "Chain is not set. Please set it with build_chain method."
        if not self.retrieve:
            response = self.chain.invoke(question)
        else:
            response = self.chain.invoke({self.question_variable: question})
        return response