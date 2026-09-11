import os
from abc import ABC
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class BaseAgent(ABC):
    def __init__(self, model: str):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
