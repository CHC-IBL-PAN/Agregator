import pandas as pd
import numpy as np
from tqdm import tqdm
import spacy
import os
import regex as re
import json
from pymarc import MARCReader
import requests
nlp = spacy.load("pl_core_news_lg")





def open_data(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data


def get_data(url: str) -> list:
    responses = []
    while url:
        url = requests.get(url)
        if url.status_code == 200:
            url = url.json()
            responses.append(url)
            url = url["nextPage"]
            print(f"Downloading: {url}")
        else:
            print("Error while accessing API")
    print("Download complete")
    return responses


def get_subj(sub: str, header: str, field_numbers: list) -> dict:
    responses = get_data(f"http://data.bn.org.pl/api/authorities.json?{header}={sub}")
    subjects = []
    for response in responses:
        for authority in response["authorities"]:
            for field in authority["marc"]["fields"]:
                for field_number in field_numbers:
                    if field_number in field:
                        for i in field:
                            subjects.append(list(field[i]["subfields"][-1].values())[0])

    subjects_dict = {}
    subjects_dict[sub] = subjects
    return subjects_dict


def prepare_fbc_subjects(path: str) -> list:
    SUBJECTS_ALL = pd.read_csv(path)
    subjects_fbc = SUBJECTS_ALL["0"].values.tolist()
    return [x for x in list(set(subjects_fbc)) if str(x) != "nan"]


def subject_matcher(path: str, subjects: dict) -> list:
    subjects_fbc = prepare_fbc_subjects(path)
    subjects_fbc_with_dbn = [x.replace("DBN", "").strip() for x in subjects_fbc]
    subjects_dbn = []
    for subject in list(subjects.values())[0]:
        subjects_dbn.append(subject)
    return [x for x in tqdm(subjects_fbc_with_dbn) if x in subjects_dbn]


def lemmatize(term):
    lemmas = " ".join([w.lemma_ for w in nlp(term)])
    return lemmas


def get_fields_of_subj(subjects: list, fields: list) -> list:
    list_of_dicts = []
    for subject in subjects:
        subjects_with_fields = get_subj(subject, "subject", fields)
        list_of_dicts.append(subjects_with_fields)
    return list_of_dicts


def marc_to_dict(path: str, fields: list) -> dict:
    records = []
    with open(path, "rb") as f:
        reader = MARCReader(f)
        for record in reader:
            for field in fields:
                if record[field] is not None:
                    records.append(record.as_dict())