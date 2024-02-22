import instructor
from instructor import llm_validator
from typing import List
from openai import OpenAI
from pydantic import BaseModel, Field
from tqdm import tqdm
from dotenv import load_dotenv
import random
import json
import os
import csv


def anki_cards_to_csv(merged_anki_card_lists, csv_file_path):

    with open(csv_file_path, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['question', 'answer'])

        for anki_card_list in merged_anki_card_lists:
            for card in anki_card_list.cards:
                csv_writer.writerow([card.question, card.answer])


class AnkiCard(BaseModel):
    index: int = Field(..., description="Monotonically increasing ID")
    question: str = Field(description="Question from the context")
    answer: str = Field(description="Straight answer to the question")


def generate_anki(file_path, num_cards):
    load_dotenv()

    class AnkiCardList(BaseModel):
        cards: List[AnkiCard] = Field(
            ...,
            description=f"Numbered list of arbitrary extracted properties, should be exactly {num_cards}",
        )

    CHUNK_SIZE = 32*1000  # a bit of padding

    with open(file_path, 'r') as f:
        base = f.read()

    chunks = [base[i:i+CHUNK_SIZE] for i in range(0, len(base), CHUNK_SIZE)]
    TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')

    client = instructor.patch(OpenAI(
        api_key=TOGETHER_API_KEY,
        base_url='https://api.together.xyz',
    ), mode=instructor.Mode.JSON)

    all_anki_card_lists = []

    for i, chunk in enumerate(tqdm(chunks)):
        resp = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente de IA",
                },
                {
                    "role": "user",
                    "content": f"Genera ANKI del siguiente texto: {base}",
                }
            ],
            response_model=AnkiCardList,
        )

        all_anki_card_lists.append(resp)

    middle = random.choice(['cat', 'dog', 'bird', 'butterfly',
                            'lion', 'tiger', 'orca'])

    prefix = random.randint(1, 100)
    suffix = random.randint(1, 100)

    csv_file_path = 'processed/' + \
        str(prefix) + '_' + middle + '_' + str(suffix) + '_deck.csv'

    if not os.path.exists('processed'):
        os.makedirs('processed')

    anki_cards_to_csv(all_anki_card_lists, csv_file_path)

    return csv_file_path
