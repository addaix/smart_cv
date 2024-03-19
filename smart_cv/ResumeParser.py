from docxtpl import DocxTemplate
from tqdm import tqdm
import os
import json
from dataclasses import dataclass
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.abspath(os.path.join(dir_path, os.pardir))
os.sys.path.append(parent_path)
print(parent_path)
from file_dialoger import File_Dialoger


class ContentRetriever(File_Dialoger):
    """ Class to parse a resume and fill a template with the information retrieved by LLM API requests.
    Args:
        cv_path (str): Path to the resume to parse.
        template_path (str): Path to the template to fill.
        prompts (dict or str): A dict of prompts for each information to retrieve or a path to a json file containing the prompts.
        api_key (str): OpenAI API key."""
    
    def __init__(self, cv_path: str, prompts: None, api_key=None, **kwargs):
        self.api_key = api_key
        self.__empty_label = kwargs.get("empty_label", "To be completed")
        self._cv_path = cv_path
        super().__init__(document_path=cv_path, api_key=api_key, **kwargs)

        self.default_Preprompt = kwargs.get("Preprompt", """
                You are in charge of human ressources in an IT company. I will give you a resume and you will answer the following questions. 
                Answer has to be precise and compleate. All information has to come from the given resume. You will provide only answer without any introduction.
                If you don't find the information, write "none". 
                If you find the information answer with this pattern: "Answer: your_answer"
                
                Here is the questions you have to answer:                           
                Question : {question}
                
                Here is the resume you have to use to answer the questions:
                Resume : {resume}
                """)
                
        self.set_prompts(prompts)
        self.dict_content = {}

    def set_prompts(self, prompts):
        """Set the prompts for the information to retrieve.
        If a prompt has no corresponding blank in the template, it will be ignored.
        If an information to retrieve has no prompt, it will be ignored. And it is added to warnings."""

        if isinstance(prompts, str):
            # open json as dict
            with open(prompts, "r") as f:
                self.prompts = json.load(f)
        if isinstance(prompts, dict):
            self.prompts = prompts
        else:
            raise ValueError("prompts should be a dict or a path to a json file")
    
    def answer_filter(self, to_filter):
        return self.ask_question(f"""I will give you an answer and you filter to keep only the answer. If nothing has to be done return the same answer.
                    examples: 
                            - 'number of years of experience: 2 years' has to becom '2 years'
                            - 'Answer: As soon as possible' has to become 'As sson as possible'
                            - 'Name: John' has to become 'John'

                    Answer to filter : {to_filter}

                    """)

    def set_info_prompt(self, info_label: str, prompt: str):
        """Set the prompt for the given information."""
        self.prompts[info_label] = prompt
    
    def get_info(self, info_label, prompt="", inplace=True, **kwargs):

        if self.dict_content.get(info_label) is not None:
            return self.dict_content[info_label]

        if not prompt:
            if info_label in self.prompts:
                prompt = self.prompts[info_label]
            else:
                print(f"Warning: No prompt for {info_label}, please set it with set_info_prompt method or give it as an argument.")
                return None
        if not hasattr(self, "chain"):
            self.build_chain(self.default_Preprompt, context_variable="resume", question_variable="question")

        content = self.ask_question(prompt)
        # TODO Add checking step
        if inplace:
            self.dict_content[info_label] = content
        else:
            return content
        
    def retrieve_content(self, pre_prompt, mapping, inplace=True):
        self.build_chain(pre_prompt, context_variable="resume", question_variable="mapping")
        content = self.ask_question(mapping)       
        print(content)
        # start before { and end after }
        content = content[content.find("{")-1:content.find("}")+1]
        content=content.replace("'", '"')
        print(content)
        if inplace:
            self.dict_content = json.loads(content)
        else:
            return json.loads(content)
    
    def retrieve_one(self, label, prompt, inplace=True):
        
        
    def label_empty_content(self, empty_label=None):
        if empty_label is None:
            self.__empty_label = "To be completed"
        for k, v in self.dict_content.items():
            if "none" in v.lower():
                self.dict_content[k] = f"{k} : {self.__empty_label}"
    
    def parse(self):
        """Parse the resume and put information in the dict_content."""
        for key in tqdm(self.prompts.keys()):
            self.dict_content[key] = self.get_info(key, inplace=False)

        
    def save_info(self, save_path):
        with open(save_path, "w") as f:
            json.dump(self.dict_content, f)
    
    def load_info(self, info_path):
        """Load the information from a json file."""
        with open(info_path, "r") as f:
            self.dict_content = json.load(f)
    
    def print_info(self, info_label=None):
        if info_label is not None:
            print(f"----------------- {info_label} -----------------")
            print(self.dict_content[info_label])
        else:
            for info_label, content in self.dict_content.items():
                print(f"----------------- {info_label} -----------------")
                print(content)


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