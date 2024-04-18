"""Module to parse a resume and fill a template with the information retrieved by LLM API requests."""

from docxtpl import DocxTemplate  # pip install docxtpl
import os
from oa import prompt_function, chat
import json
from typing import Mapping, Union, List
from functools import partial
from dataclasses import dataclass
from meshed import provides
from smart_cv.VectorDB import ChunkDB
from smart_cv.util import num_tokens

DEBUG = False


def debug(message):
    if DEBUG:
        print(message)


def get_chunk_size(cv_len, cv_tokens, prompt_tokens, max_tokens):
    assert (
        max_tokens > prompt_tokens
    ), f"The prompt is too long: limit is {max_tokens} tokens, prompt is {prompt_tokens} tokens"
    if cv_tokens < max_tokens - prompt_tokens:
        nb_chunks = 1
    elif cv_tokens == max_tokens - prompt_tokens:
        nb_chunks = 1
    else:
        nb_chunks = cv_tokens // (max_tokens - prompt_tokens) + 1
    return cv_len // nb_chunks


def replace_none_in_json(json_data, empty_label):
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

@dataclass
@provides("raw_dict_content")
class ContentRetriever():
    """Class to parse a resume and fill a template with the information retrieved by LLM API requests.
    Args:
        cv_path (str): Path to the resume to parse.
        template_path (str): Path to the template to fill.
        prompts (dict or str): A dict of prompts for each information to retrieve or a path to a json file containing the prompts.
        api_key (str): OpenAI API key."""
    cv_text: str
    prompts: Mapping
    stacks: str
    json_example: str
    #language_list: List[str]
    #empty_label: str 
    #optional_content: Mapping
    #language: str = "automatic" # automatic : detect the language of the text, english, french, ...
    api_key: str = None
    chunk_overlap: int = 100
    temperature: float = 0.0
    def __post_init__(
        self,
        
        **kwargs,
    ):
        self.dict_content = {}
        self.chat = partial(chat, temperature=self.temperature)
        prompt_tokens = num_tokens(
            self.content_request("", "")
        ) + num_tokens(str(self.prompts))
        cv_tokens = num_tokens(self.cv_text)
        max_tokens = 4000  # TODO : Find a way to get the max tokens from the API

        chunk_size = get_chunk_size(len(self.cv_text), cv_tokens, prompt_tokens, max_tokens)
        self.db = ChunkDB(
            {str(kwargs.get('cv_name', 'cv')): self.cv_text}, chunk_size=chunk_size, chunk_overlap=self.chunk_overlap
        )

        debug(f"Chunk size: {chunk_size}")

    def content_request(self, json_string=None, chunk_context=None, stacks=None, json_example=None):
        if stacks is None:
            stacks = self.stacks
        if json_example is None:
            json_example = self.json_example
        content_prompt = f"""
                I will give you a resume and you will fill the provided json. 
                The keys have to be respected and the corresponding description will be replaced by the retrieved information. 
                Answer has to be precise, compleate and contains as much as possible informations of the resume. All information has to come from the given resume.
                If you don't find the information, write "none". 

                Here is an example to guide you:
                    {json_example}

                Here is the json you have to fill:                           
                Json : {json_string}
                
                Give directly the json and preserve the format (double quotes for keys).

                Here is the resume you have to base on: {chunk_context} 
                                   
                Here are keywords of technical stack that should be found in the resume to fill 'skills': 
                {stacks}
                """
        return content_prompt

    def aggregate_dicts(self, dict_list: List[Mapping]):
        """Aggregate the information of a list of dictionaries."""
        if len(dict_list) == 1:
            return dict_list[0]
        result = dict_list[0]
        for d in dict_list[1:]:
            try:
                result_str = self.ask_question(
                    f"""Aggregate the 2 following dicts 
                                       values without repetitions and return the dict with 
                                       same keys and aggregated values: 
                                       first dict: {str(result)}
                                        second dict: {str(d)}"""
                )
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
                    result[k] = self.ask_question(
                        f"Aggregate content the 2 following contents without repetitions: {str(result[k])} and {str(v)}"
                    )
                else:
                    result[k] = v
        return result

    def retrieve_content(self, json_string: str = None, inplace=True, verbose=False):
        """Given a mapping of information to retrieve, retrieve all the information and put it in the dict_content.
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
            content = self.chat(self.content_request(
                    json_string=json_string, chunk_context=chunk_context,  stacks=self.stacks, json_example=self.json_example
                 ))
            try:
                content_json = json.loads(content)
            except json.JSONDecodeError as e:
                content = self.chat(
                    f"This json is not well formatted {content}. Here is the error{e}). Please correct it and return the corrected json."
                )
                print("The json is not well formatted. Trying again...")
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
    
    def __call__(self):
        self.retrieve_content()
        return self.dict_content
    
def detect_language(cv_text:str, language_list: List[str], chat):
    """Detect the language of the text."""
    lang = chat(f"Detect the language of the following text: {cv_text} \n Return english, french, spanish or potuguese.")
    for l in language_list:
        if l.lower() in lang.lower():
            return l.lower()
    return lang.split(":")[1].lower()
    
@provides("translated_dict_content")
def translate_content(dict_content, cv_text:str, language:str="automatic", *,language_list: List[str], chat):
    """Translate the content in the given language."""

    if language == "automatic":
        language = detect_language(cv_text, language_list, chat)
    if language == "english":
        return dict_content
    else:
        translated_content = chat(f"""Translate the values of the following json in : {language}  
                                            Keep the keys as they are and translate the values. Return the translated json.
                                            Do not translate 'none'.
                                            Keep json fromat (double quotes).
                                            Content: {str(dict_content)} """)
    return json.loads(translated_content)

@provides("labeled_optional_content")
def has_content_labelling(dict_content, optional_content: List[str]):
    """Add a boolean to the dict_content for each optional content. This informs if the content is present in the resume or not."""
    updated_content = dict_content.copy()
    for k in optional_content:
        v = dict_content[k]
        if isinstance(v, str):
            if "none" in v.lower():
                updated_content["has_" + k] = False
            else:
                updated_content["has_" + k] = True
    
    return updated_content

def bytes_content(dict_content):
    import json
    return json.dumps(dict_content).encode('utf-8')

# def retrieve_one(label, prompt=None, inplace=True):
#     """Retrieve the information for the given label and put it in the dict_content if inplace is True. Else return the content."""
#     if prompt is not None:
#         self.prompts[label] = prompt
#     else:
#         assert label in self.prompts, f"Please set a prompt for {label} ."
#     new_content = self.retrieve_content({label: self.prompts[label]}, inplace=False)
#     if inplace:
#         self.dict_content.update(new_content)
#     return new_content

def save_content(dict_content, save_path):
    """Save the information in a json file."""
    with open(save_path, "w") as f:
        json.dump(dict_content, f)

def load_content(content_path):
    """Load the information from a json file."""
    with open(content_path, "r") as f:
        dict_content = json.load(f)
    return dict_content

@provides("labeled_empty_content")
def label_empty_content(
    dict_content: dict, empty_label: str
):  
    updated_content = dict_content.copy()
    return replace_none_in_json(updated_content, empty_label)

def print_content(dict_content, content_label=None):
    if content_label is not None:
        print(f"----------------- {content_label} -----------------")
        print(dict_content[content_label])
    else:
        for content_label, content in dict_content.items():
            print(f"----------------- {content_label} -----------------")
            print(content)

    # # TODO: Can we do this whole pipeline in an immutable chain?
    # def __call__(self):
    #     self.retrieve_content()
    #     self.has_content_labelling()
    #     self.dict_content = self.translate_content()
    #     # doing it the immutable way:
    #     dict_content = self.dict_content
    #     dict_content = self.label_empty_content(dict_content, self.empty_label)
    #     return dict_content
    


from typing import Mapping

@dataclass
class TemplateFiller:
    """Class to fill a docx template with the information provided in the content dict.
    Warning: The template should have the same labels as the keys of the content dict.
    """

    template_path: str
    content: Mapping

    def __post_init__(self):
        self.template = DocxTemplate(self.template_path)
        self.blanks = self.template.undeclared_template_variables

    def fill_template(self, **kwargs):
        """Fill the template with the information in the dict_content."""
        self.template.render(
            {label: (self.content.get(label, "")) for label in self.blanks}
        )

    def save_template(self, save_path):
        """Fill the template with the information in the dict_content."""
        if not self.template.is_rendered:
            self.fill_template()
        self.template.save(save_path)

    def __call__(self, save_path):
        self.save_template(save_path)

def template_bytes(template_path: str, content: Mapping):
    """Return the bytes of the filled template."""
    filler = TemplateFiller(template_path, content)
    filler.fill_template()
    return filler.template.get_docx()