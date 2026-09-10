import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
try:
    print('Calling generate_content with gemini-3.7-flash...')
    res = client.models.generate_content(
        model='gemini-3.7-flash',
        contents='Parle moi de la maison des esclaves',
        config=types.GenerateContentConfig(
            tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=['fileSearchStores/goreemaisonesclaves-vxqxk0scxpj5']))]
        )
    )
    print('Result length:', len(res.text))
    print('Excerpt:', res.text[:300])
except Exception as e:
    print('Exception:', e)
