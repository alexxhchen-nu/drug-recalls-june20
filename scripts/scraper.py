from firecrawl import Firecrawl
from firecrawl.types import ScrapeOptions
from firecrawl.v2.types import ParseOptions
from dotenv import load_dotenv
import os

# Load API key 
load_dotenv()  # Load environment variables from .env file
# get the API key for Firecrawl
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")

firecrawl = Firecrawl(api_key=str(FIRECRAWL_API_KEY))

# Scrape a website:
scrape_result = firecrawl.scrape('firecrawl.dev', formats=['markdown', 'html'])
print(scrape_result)

# parsing file
parsed = firecrawl.parse(
    b"<!DOCTYPE html><html><body><h1>Python Parse</h1></body></html>",
    filename="upload.html",
    content_type="text/html",
    options=ParseOptions(formats=["markdown"]),
)

print(parsed.markdown)