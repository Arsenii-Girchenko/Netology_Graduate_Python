import json
import requests

FREE_DICT_API_HOST = 'https://api.dictionaryapi.dev/api/v2/entries/en'

def get_use_example(word, dictionary_api_url=FREE_DICT_API_HOST):
    url = dictionary_api_url
    example_list = []
    req_url = f'{url}/{str(word)}'
    response = json.loads(requests.get(req_url).text)
    for param in response:
        for category in param.keys():
            if category == 'meanings':
                for content in param[category]:
                    for criterion in content.keys():
                        if criterion == 'definitions':
                            for facts in content[criterion]:
                                for k in facts.keys():
                                    if k == 'example':
                                        example_list.append(facts[k])
    return example_list