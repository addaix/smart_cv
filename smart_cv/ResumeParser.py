from docxtpl import DocxTemplate
from tqdm import tqdm
import os
import json
from typing import Mapping, Union, List
from dataclasses import dataclass
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.abspath(os.path.join(dir_path, os.pardir))
os.sys.path.append(parent_path)
print(parent_path)
from file_dialoger import File_Dialoger
from VectorDB import ChunkDB
from smart_cv.util import num_tokens_doc, num_tokens_from_string, load_full_text

DEBUG = False
def debug(message):
    if DEBUG:
        print(message)

def get_chunk_size(cv_len, cv_tokens, prompt_tokens, max_tokens):
    assert max_tokens>prompt_tokens, f"The prompt is too long: limit is {max_tokens} tokens, prompt is {prompt_tokens} tokens"
    if cv_tokens<max_tokens-prompt_tokens:
        nb_chunks = 1
    elif cv_tokens==max_tokens-prompt_tokens:
        nb_chunks = 1
    else:
        nb_chunks = cv_tokens//(max_tokens-prompt_tokens) + 1
    return cv_len//nb_chunks

def replace_none_in_json(json_data, empty_label="To be completed"):
        if isinstance(json_data, dict):
            for key in json_data:
                if json_data[key] == "none":
                    json_data[key] = empty_label
                else:
                    replace_none_in_json(json_data[key], empty_label)
        elif isinstance(json_data, list):
            for i in range(len(json_data)):
                if isinstance(json_data[i], str) and "none" in json_data[i].lower():
                    json_data[i] = json_data[i].replace("none", empty_label)
                else:
                    replace_none_in_json(json_data[i], empty_label)
        return json_data

class ContentRetriever(File_Dialoger):
    """ Class to parse a resume and fill a template with the information retrieved by LLM API requests.
    Args:
        cv_path (str): Path to the resume to parse.
        template_path (str): Path to the template to fill.
        prompts (dict or str): A dict of prompts for each information to retrieve or a path to a json file containing the prompts.
        api_key (str): OpenAI API key."""
    
    def __init__(self, cv_path: str, prompts: Mapping, api_key: str=None, optional_content=None, **kwargs):
        self.api_key = api_key
        self.__empty_label = kwargs.get("empty_label", "To be completed")
        self._cv_path = cv_path
        self.optional_content = optional_content
        
        self.dict_content = {}
        self.prompts = prompts

        prompt_tokens = num_tokens_from_string(self.content_request("","")) + num_tokens_from_string(str(self.prompts))
        cv_tokens = num_tokens_doc(self._cv_path)
        chunk_overlap = kwargs.get("chunk_overlap", 100)
        max_tokens = 4000 # TODO : Find a way to get the max tokens from the API

        content = load_full_text(self._cv_path)
        chunk_size = get_chunk_size(len(content), cv_tokens, prompt_tokens, max_tokens)
        self.db = ChunkDB({self._cv_path: content}, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        super().__init__(api_key=api_key, retrieve=False)

        debug(f"Chunk size: {chunk_size}")
    
    def content_request(self, json_string=None, chunk_context=None):
        content_prompt = f"""
                I will give you a resume and you will fill the provided json. 
                The keys have to be respected and the corresponding description will be replaced by the retrieved information.
                Answer has to be precise, compleate and contains as much as possible informations of the resume. All information has to come from the given resume.
                If you don't find the information, write "none". 

                Here is an example to guide you:
                    example of original json : 
                        "JobTitle": Give the job title of the candidate,
                        "avaibility": When is the candidate available to start,
                        "mobility": Is the candidate ready to move, if yes where,
                        "seniority": Number of years of experience,
                        "skills": List the technical skills of the candidate,
                        "certifications": List the certifications of the candidate related to the job,
                        "experiences": List the professional experiences of the candidate,
                        "personal_projects": List the personal projects of the candidate,
                        "languages": List the languages spoken by the candidate,
                        "education": List the studies of the candidate and provide level and date if possible
                        
                    example of the completed json : 
                        "JobTitle": "Data Scientist",
                        "avaibility": "As soon as possible",
                        "mobility": "none",
                        "seniority": "2 years",
                        "skills": "Python, SQL, Machine Learning, NLP",
                        "certifications": "DataCamp, Coursera",
                        "experiences": [
                            {{"title": "Apprentice data analyst",
                                "company": "Facebook",
                                "dates": "2020-2023",
                                "description": "Worked on the user behavior analysis.",
                                "tasks": "Data cleaning of the dataset, Building the model, Testing the model, etc...",
                                "tools": "Python, TensorFlow, Pandas, Numpy, etc..."}},
                            {{   "title": "Data Scientist intern",
                                "company": "Google",
                                "dates": "2020 - 3 months",
                                "description": "Worked on the recommendation system of Youtube.",
                                "tasks": "Data cleaning of the dataset, Building the model, Testing the model, etc...",
                                "tools": "Python, TensorFlow, Pandas, Numpy, etc..."}},
                            - {{"etc..."}}
                        ],
                        "personal_projects": "Chatbot, face recognition",
                        "languages": "English(C1), French, Spanish (B2)", 
                        "education": [
                            "diploma": Master in Data Science,
                            "school": Harvard,
                            "dates": 2018-2020]

                the "etc..." indicates that you can add more information if needed. If not remove it.

                Here is the json you have to fill:                           
                Json : {json_string}
                
                Give directly the json and preserve the format.

                Here is the resume you have to base on: {chunk_context} 
                                    
                Here are keywords of technical stack that should be found in the resume to fill 'skills': 
                 C,, Perl, Ruby, MatLab, Mathematica, Assembleur, VB, XML, JEE, J2EE, JavaScript, PHP, R,, CSS, C\+\+, IOS, Swift, Android, Kotlin, Flutter, Dart, Rust, Ionic, Cordova, Reactnative, Xamarin, Babylon.js, C\#, F\#, WordPress, ThreeJS, WebGL,
                TensorFlow, Spark, Spring, Angular, Structs, Ember, Vue, Django, React, .NET,, .NET Core, Cocoapods, Osgi, Selenium, QA, Nest, Express, Symphony, Falcon, ASP.NET, WinDev, Flask, PySpark, Hibernate,
                Hive, Impala, Oracle, MySQL, Acess, SQL, SQL Server, PostgreSQL, Mongo, MariaDB, DBA,
                API, Unit Testing, Test Unitaire, Azure, Docker, Bamboo, Kubernetes, Jenkins, Jasmine, Karma, MVC, AWS,
                Git, Tortoise, TFS, CVS, SVN, MVC, GNU RCS, GNU CSSC, CVSNT, GNU arch, Darcs, DCVS, Monotone, Codeville, Mercurial, Bazaar, Fossil, Veracity, Pijul, SCCS, PVCS, Rational ClearCase, Harvest, CMVC, Visual SourceSafe, AccuRev SCM, Sourceanywhere, Team Foundation Server, Rational Synergy, Rational Team Concert, BitKeeper, Plastic SCM, IIS active directory, 2IS,
                Datawarehouse, Machine Learning, NLP, DeepLearning, Réseau de Neurones, kNN, k\-NN, Régression Linéaire, SVM, Régression Logistique, Arbre de Décission, Fôrets Aléatoires, gradient boosting, PCA, Analyse en Composantes Principales, DataLake, DataFactory, PowerBI, Tableau, Qlikesense, GCP, OpenCV, Computer Vision, 
                Gestion, Organization, Management, Agile, Scrum, Trello, JIRA, MS Project, Confluence, Sprint, GANTT, Specifications, Redaction, Cahier de charges, Workshop, Atelier, AMOA, PMO
                """
        return content_prompt
        
    def aggregate_dicts(self, dict_list: List[Mapping]):
        """Aggregate the information of a list of dictionaries."""
        if len(dict_list)==1:
            return dict_list[0]
        result = dict_list[0]
        for d in dict_list[1:]:
            try:
                result_str = self.ask_question(f"""Aggregate the 2 following dicts 
                                       values without repetitions and return the dict with 
                                       same keys and aggregated values: 
                                       first dict: {str(result)}
                                        second dict: {str(d)}""")
            except Exception as e:
                print(e, "Trying again...")
                return self.aggregate_dict_values(dict_list)
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError as e:
                print("The json is not well formatted. Trying again...")
                return self.aggregate_dict_values(dict_list)
        return result

    def aggregate_dict_values(self, dict_list: List[Mapping]):
        """Aggregate the information of a list of dictionaries."""
        result = {}
        for d in dict_list:
            for k, v in d.items():
                if k in result:
                    result[k] = self.ask_question(f"Aggregate content the 2 following contents without repetitions: {str(result[k])} and {str(v)}")
                else:
                    result[k] = v
        return result

    def retrieve_content(self, json_string:str=None, inplace=True, verbose=False):
        """ Given a mapping of information to retrieve, retrieve all the information and put it in the dict_content.
        example:    mapping = {"JobTitle": "Give the job title of the candidate",  
                            "avaibility": "When is the candidate available to start" }

                    Returns: {"JobTitle": "Data Scientist",
                            "avaibility": "As soon as possible"}
            """
        content_list = []
        if json_string is None:
            json_string = self.prompts

        for segment_index in self.db.segments:
            chunk_context = self.db.segments[segment_index]
            content=self.ask_question(self.content_request(json_string=json_string, chunk_context=chunk_context))
            try :
                content_json = json.loads(content)
            except json.JSONDecodeError as e:
                content = self.ask_question(f"This json is not well formatted {content}. Here is the error{e}). Please correct it and return the corrected json.")
                print("The json is not well formatted. Trying again...")
                print(content)
                try:
                    content_json = json.loads(content)
                except json.JSONDecodeError as e:
                    print("The json is still not well formatted. Please correct it.")
                    return e
            content_list.append(content_json)
        full_content = self.aggregate_dicts(content_list)
        if inplace:
            self.dict_content = full_content
        return full_content
    
    def has_content_labelling(self):
        for k in self.optional_content:
            v = self.dict_content[k]
            if isinstance(v, str):
                if "none" in v.lower():
                    self.dict_content["has_"+k] = False
                else:
                    self.dict_content["has_"+k] = True                
    
    def retrieve_one(self, label, prompt=None, inplace=True):
        """Retrieve the information for the given label and put it in the dict_content if inplace is True. Else return the content."""
        if prompt is not None:
            self.prompts[label] = prompt
        else:
            assert label in self.prompts, f"Please set a prompt for {label} ."
        new_content = self.retrieve_content({label: self.prompts[label]}, inplace=False)
        if inplace:
            self.dict_content.update(new_content)
        return new_content
        
        
    def save_content(self, save_path):
        with open(save_path, "w") as f:
            json.dump(self.dict_content, f)
    
    def load_content(self, content_path):
        """Load the information from a json file."""
        with open(content_path, "r") as f:
            self.dict_content = json.load(f)
    
    def label_empty_content(self,empty_label="To be completed"):
        self.dict_content = replace_none_in_json(self.dict_content, empty_label)
    
    def print_content(self, content_label=None):
        if content_label is not None:
            print(f"----------------- {content_label} -----------------")
            print(self.dict_content[content_label])
        else:
            for content_label, content in self.dict_content.items():
                print(f"----------------- {content_label} -----------------")
                print(content)

    def __call__(self):
        self.retrieve_content()
        self.has_content_labelling()
        self.label_empty_content()
        return self.dict_content


from typing import Mapping
@dataclass
class TemplateFiller:
    """ Class to fill a docx template with the information provided in the content dict.
    Warning: The template should have the same labels as the keys of the content dict."""
    template_path: str
    content: Mapping

    def __post_init__(self):
        self.template = DocxTemplate(self.template_path)
        self.blanks = self.template.undeclared_template_variables

    def fill_template(self, **kwargs):
        """Fill the template with the information in the dict_content. """
        self.template.render({label: (self.content.get(label, "")) for label in self.blanks})

    def save_template(self, save_path):
        """Fill the template with the information in the dict_content."""
        if not self.template.is_rendered:
            self.fill_template()
        self.template.save(save_path)
    
    def __call__(self, save_path):
        self.save_template(save_path)
    