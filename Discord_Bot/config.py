# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('DISCORD_TOKEN')
    PREFIX = os.getenv('COMMAND_PREFIX', '!')
    OWNER_ID = int(os.getenv('OWNER_ID', 0))
    ACTIVITY_TYPE = os.getenv('ACTIVITY_TYPE', 'watching over BlazeX')
    ACTIVITY_NAME = os.getenv('ACTIVITY_NAME', 'MADE BY KAIRO.DEV')
    
    @classmethod
    def validate(cls):
        if not cls.TOKEN:
            raise ValueError("No token found! Set DISCORD_TOKEN in .env file")