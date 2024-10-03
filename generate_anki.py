import os
import csv
import json
import random
from typing import List, Union
from tqdm import tqdm
from openai import OpenAI
from pydantic import BaseModel, Field
from io import StringIO

class AnkiCard(BaseModel):
    question: str = Field(description="Question from the context")
    answer: str = Field(description="Straight answer to the question")

class AnkiCardList(BaseModel):
    cards: List[AnkiCard] = Field(..., description="List of Anki cards")

def get_api_key():
    api_key = os.environ.get('API_KEY')
    if not api_key:
        raise ValueError("API_KEY environment variable is not set")
    return api_key

def generate_anki(input_data: Union[str, StringIO], num_cards: int, is_file: bool = False) -> StringIO:
    CHUNK_SIZE = 32000  # Adjust as needed
    
    if is_file:
        with open(input_data, 'r') as f:
            content = f.read()
    else:
        content = input_data
    
    chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]
    
    client = OpenAI(
        api_key=get_api_key(),
        base_url='https://api.deepseek.com'
    )
    
    all_anki_cards = []
    
    system_prompt = """
    You are an ANKI builder that is building ANKI decks. Parse the given text and create Anki cards in JSON format.
    Each card should have a 'question' and an 'answer'.
    EXAMPLE OUTPUT:
    {
        "cards": [
            {
                "question": "What is the capital of France?",
                "answer": "Paris"
            },
            {
                "question": "Who wrote 'Romeo and Juliet'?",
                "answer": "William Shakespeare"
            }
        ]
    }
    """
    
    for chunk in tqdm(chunks):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate {num_cards} Anki cards from the following text: {chunk}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=2000  # Adjust as needed
        )
        
        try:
            anki_card_list = AnkiCardList.parse_obj(json.loads(response.choices[0].message.content))
            all_anki_cards.extend(anki_card_list.cards)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from chunk. Skipping this chunk.")
        except Exception as e:
            print(f"Error processing chunk: {e}")
    
    # Ensure we have exactly num_cards
    all_anki_cards = all_anki_cards[:num_cards]
    
    # Create a StringIO object to hold the CSV data
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)
    for card in all_anki_cards:
        csv_writer.writerow([card.question, card.answer])
    
    # Reset the buffer's position to the beginning
    csv_buffer.seek(0)
    
    return csv_buffer

# Usage
if __name__ == "__main__":
    # Example 1: Using a file
    input_file = "mexican_history.md"
    num_cards = 10
    csv_buffer_from_file = generate_anki(input_file, num_cards, is_file=True)
    print(f"Anki cards generated from file. CSV content:\n{csv_buffer_from_file.getvalue()}")

    # Example 2: Using in-memory content
    #content = """Your content here"""  # Replace with actual content
    #csv_buffer_from_memory = generate_anki(content, num_cards, is_file=False)
    #print(f"Anki cards generated from memory. CSV content:\n{csv_buffer_from_memory.getvalue()}")
