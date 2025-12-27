# Copyright 2024 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import json
import math
import requests
from typing import Dict, Any, Optional


def format_indicator(solution_str: str, modality: str) -> bool:
    regexs = {
        "image": [
            re.compile( r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:safe\r?\nCategory:None\r?\n</answer>$', re.DOTALL),
            re.compile( r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:unsafe\r?\nCategory:(?!None\r?\n)[^\r\n]+\r?\n</answer>$', re.DOTALL),
        ],
        "other": [
            re.compile( r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:safe\r?\nResponse:safe\r?\nCategory:None\r?\n</answer>$', re.DOTALL),
            re.compile( r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:unsafe\r?\nResponse:safe\r?\nCategory:(?!None\r?\n)[^\r\n]+\r?\n</answer>$', re.DOTALL),
            re.compile( r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:safe\r?\nResponse:unsafe\r?\nCategory:(?!None\r?\n)[^\r\n]+\r?\n</answer>$', re.DOTALL),
            re.compile( r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:unsafe\r?\nResponse:unsafe\r?\nCategory:(?!None\r?\n)[^\r\n]+\r?\n</answer>$', re.DOTALL),
        ]
    }
    if modality == "image":
        key = "image"
    else:
        key = "other"
    for regex in regexs[key]:
        if regex.match(solution_str):
            return True
    return False


def parse_solution_strict(solution_str: str, modality: str):
    safe_pattern = {
        "image": re.compile(
            r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:(safe)\r?\nCategory:None\r?\n</answer>$',
            re.DOTALL
        ),
        "other": re.compile(
            r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:(safe)\r?\nResponse:(safe)\r?\nCategory:None\r?\n</answer>$',
            re.DOTALL
        )
    }

    unsafe_pattern = {
        "image": re.compile(
            r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:(unsafe)\r?\nCategory:([^\r\n]+)\r?\n</answer>$',
            re.DOTALL
        ),
        "other": re.compile(
            r'^<think>.*?</think>\r?\n<answer>\r?\nRequest:(safe|unsafe)\r?\nResponse:(safe|unsafe)\r?\nCategory:([^\r\n]+)\r?\n</answer>$',
            re.DOTALL
        )
    }
    if modality == "image":
        key = "image"
    else:
        key = "other"
    m = safe_pattern[key].match(solution_str)
    if m:
        if modality == "image":
            return m.group(1), "", ""
        else:
            return m.group(1), m.group(2), ""
    m = unsafe_pattern[key].match(solution_str)
    if m:
        if modality == "image":
            return m.group(1), "", m.group(2).strip()
        else:
            return m.group(1), m.group(2), m.group(3).strip()
    return "", "", ""


def compute_similarity(text1: str, text2: str, url: str, timeout: int = 30) -> float:
    try:
        payload = {"text1": text1, "text2": text2}
        response = requests.post(f"{url}/similarity", json=payload, timeout=timeout)
        if response.status_code == 200:
            result = response.json()
            return result.get("similarity", 0.0)
        else:
            print(f"Sentence transformer API error: {response.status_code}")
            return 0.0
    except Exception as e:
        print(f"Error calling sentence transformer API: {e}")
        return 0.0


def is_predefined_category(category: str) -> bool:
    if not category:
        return False
    
    c_s_pattern = re.compile(r'^C\d+S\d+$')
    if c_s_pattern.match(category):
        return True
    
    c_pattern = re.compile(r'^C\d+$')
    if c_pattern.match(category):
        return True
    
    return False


def compute_score(solution_str: str,
                  ground_truth: str = "",
                  extra_info: Optional[Dict[str, Any]] = None,
                  sentence_transformer_url: str = "0.0.0.0:8002",
                  sentence_transformer_timeout: int = 30,
                  sentence_transformer_threshold: float = 0.7,
                  sentence_transformer_semaphore=None,) -> float:
    query_label = extra_info["query_label"]
    response_label = extra_info["response_label"]
    category_id = extra_info["category"]
    category_name = extra_info["original_category"]
    modality = extra_info["modality"]
    synonymous_phrase = extra_info["synonymous_phrase"]
    need_ood = category_id == ""

    if not format_indicator(solution_str, modality):
        return 0.0
    total_reward = 0.0
    answer_query_label, answer_response_label, answer_category = parse_solution_strict(solution_str, modality)

    if query_label == answer_query_label:
        if modality == "image":
            total_reward += 2.0
        else:
            total_reward += 1.0

    if modality != "image" and response_label == answer_response_label:
        total_reward += 1.0
    
    if (query_label == "safe" and response_label == "safe") or (answer_query_label == "safe" and answer_response_label == "safe"):
        return total_reward
    
    if need_ood:
        if is_predefined_category(answer_category):
            category_reward = 0.0
        else:   
            category_reward = 0.5
            similarities = []
            if sentence_transformer_url and answer_category and category_name:
                if sentence_transformer_semaphore:
                    with sentence_transformer_semaphore:
                        similarities.append(compute_similarity(
                            answer_category, 
                            category_name, 
                            sentence_transformer_url, 
                            sentence_transformer_timeout or 30
                        ))
                        for synonymous_phrase in synonymous_phrase:
                            similarities.append(compute_similarity(
                                answer_category, 
                                synonymous_phrase, 
                                sentence_transformer_url, 
                                sentence_transformer_timeout
                            ))
                else:
                    similarities.append(compute_similarity(
                        answer_category, 
                        category_name, 
                        sentence_transformer_url, 
                        sentence_transformer_timeout
                    ))
                    for synonymous_phrase in synonymous_phrase:
                        similarities.append(compute_similarity(
                            answer_category, 
                            synonymous_phrase, 
                            sentence_transformer_url, 
                            sentence_transformer_timeout
                        ))
                sim_bonus_1 =(max(similarities) - 0.7) / (1 - 0.7) * 0.5
                sim_bonus_2 =(sum(similarities) / len(similarities) - 0.6) / (1 - 0.6) * 0.5
                if sim_bonus_1 > 0.0 or sim_bonus_2 > 0.0:
                    category_reward += max(sim_bonus_1, sim_bonus_2)
        
        total_reward += category_reward
    elif is_predefined_category(answer_category): 
        total_reward += 1.0 if answer_category == category_id else 0.5 
    
    return total_reward
