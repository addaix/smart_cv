"""This module is used to check informations in a cv and give feedbacks regarding specified rules."""

import sys
from functools import cached_property
sys.path.append('..')
from file_dialoger import File_Dialoger

class CriteriaChecker:
    def __init__(self, criteria: list[str], document, *args, **kwargs):
        self.chat_model = File_Dialoger(retrieve=False, *args, **kwargs)
        self.document = str(document)
        self.pre_prompt = kwargs.get("pre_prompt", """Given the provided resume, check the following criterion 
                                     and answer with yes if the criterion is verified and No otherwise.
                                    Instruction : {instruction}
                                    Resume: {resume}""")
        self.criteria = criteria
        
    def check_criterion(self, criterion: str, verbose: bool = False):
        question = self.pre_prompt.format(instruction=criterion, resume=self.document)
        res = self.chat_model.ask_question(question)
        if verbose:
            print(res)
        return bool("yes" in res.lower())
    
    def check_all(self, verbose: bool = False):
        results = {}
        for criterion in self.criteria:
            results[criterion] = self.check_criterion(criterion, verbose=verbose)
        return results

    @cached_property
    def status(self):
        return self.check_all()      
    
    @cached_property
    def score(self):
        return sum(self.status.values())/len(self.status)
    
    def add_criterion(self, criterion: str):
        self.criteria.append(criterion)
        self.status.update({criterion: self.check_criterion(criterion)})
        self.score = sum(self.status.values())/len(self.status)

    def remove_criterion(self, criterion: str):
        self.criteria.remove(criterion)
        self.status.pop(criterion)
        self.score = sum(self.status.values())/len(self.status)

    def feedback(self):
        """ Returns the non satisfied criteria """
        return {criterion: status for criterion, status in self.status.items() if not status}