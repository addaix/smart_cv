# 20:03:2024
Issue : LLM response is to general, it needs to get aware of our jargon
example : when asking for DepSecOps skills it returns: web development, Information system ...
We would expect gitlabci, helm-chart, terraform, Kubernetes, docker, docker-compose,etc...

Suggestions: 
- give as context a jargon for every job category but suppose to list a finite number of jobs and list stacks
- Learn a representation of kewords and job category from corpus of DTs.
- Fine tunning => build a dataset. How? What?

TODO : evaluation pipeline
____________________

Issues: Parsing LLM response to get a mapping

suggestions:
- ask for yaml format
- GPT4 json output format: to be explored
- Give example to LLM

Solution used:
1- Give example of keys and values. Ask for json format
2- Start string to { character to avoid intro/context like : "The json asked is : ..." or "Answer: ..."
3- Then parse with json.loads method
