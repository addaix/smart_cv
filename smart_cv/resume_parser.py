from docxtpl import DocxTemplate  # pip install docxtpl
import os
import json
from typing import Mapping, Union, List
from dataclasses import dataclass

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.abspath(os.path.join(dir_path, os.pardir))
os.sys.path.append(parent_path)
print(parent_path)
from file_dialoger import FileDialoger
from VectorDB import ChunkDB
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


class ContentRetriever(FileDialoger):
    """Class to parse a resume and fill a template with the information retrieved by LLM API requests.
    Args:
        cv_path (str): Path to the resume to parse.
        template_path (str): Path to the template to fill.
        prompts (dict or str): A dict of prompts for each information to retrieve or a path to a json file containing the prompts.
        api_key (str): OpenAI API key."""

    def __init__(
        self,
        cv_text: str,
        prompts: Mapping, 
        stacks: str,
        json_example: str,
        language: str = "detection", # detection : detect the language of the text, english, french, ...
        api_key: str = None,
        cv_name: str = "cv",
        optional_content=None,
        **kwargs,
    ):
        self.api_key = api_key
        self.__empty_label = kwargs.get("empty_label", "To be completed")
        self.optional_content = optional_content
        self.cv_text = cv_text
        self.language = language
        self.dict_content = {}
        self.prompts = prompts
        self.stacks = stacks
        self.json_example = json_example

        prompt_tokens = num_tokens(
            self.content_request("", "")
        ) + num_tokens(str(self.prompts))
        cv_tokens = num_tokens(self.cv_text)
        chunk_overlap = kwargs.get("chunk_overlap", 100)
        max_tokens = 4000  # TODO : Find a way to get the max tokens from the API

        chunk_size = get_chunk_size(len(self.cv_text), cv_tokens, prompt_tokens, max_tokens)
        self.db = ChunkDB(
            {str(kwargs.get('cv_name', 'cv')): self.cv_text}, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        super().__init__(api_key=api_key, retrieve=False)

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
            content = self.ask_question(
                self.content_request(
                    json_string=json_string, chunk_context=chunk_context,  stacks=self.stacks, json_example=self.json_example
                )
            )
            try:
                content_json = json.loads(content)
            except json.JSONDecodeError as e:
                content = self.ask_question(
                    f"This json is not well formatted {content}. Here is the error{e}). Please correct it and return the corrected json."
                )
                print("The json is not well formatted. Trying again...")
                try:
                    content_json = json.loads(content)
                except json.JSONDecodeError as e:
                    print("The json is still not well formatted. Please correct it.")
                    return e
            print("Content retrieved: ", content_json)
            content_list.append(content_json)
        full_content = self.aggregate_dicts(content_list)
        if inplace:
            self.dict_content = full_content
        return full_content
    
    def translate_content(self, language=None):
        """Translate the content in the given language."""
        if language is None:
            language = self.language
        if language == "english":
            return self.dict_content
        translated_content = self.ask_question(f"""Translate the values of the following json in : {language}  
                                               Keep the keys as they are and translate the values. Return the translated json.
                                               Do not translate 'none'.
                                               Keep json fromat (double quotes).
                                               Content: {str(self.dict_content)} """)
        return json.loads(translated_content)

    def has_content_labelling(self):
        for k in self.optional_content:
            v = self.dict_content[k]
            if isinstance(v, str):
                if "none" in v.lower():
                    self.dict_content["has_" + k] = False
                else:
                    self.dict_content["has_" + k] = True

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

    def label_empty_content(
        self, dict_content: dict, empty_label: str = "To be completed"
    ):
        return replace_none_in_json(dict_content, empty_label)

    def print_content(self, content_label=None):
        if content_label is not None:
            print(f"----------------- {content_label} -----------------")
            print(self.dict_content[content_label])
        else:
            for content_label, content in self.dict_content.items():
                print(f"----------------- {content_label} -----------------")
                print(content)

    # TODO: Can we do this whole pipeline in an immutable chain?
    def __call__(self):
        self.retrieve_content()
        self.has_content_labelling()
        self.dict_content = self.translate_content()
        # doing it the immutable way:
        dict_content = self.dict_content
        dict_content = self.label_empty_content(dict_content)
        return dict_content


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
