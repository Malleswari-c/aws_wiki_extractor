import requests
#importing pdfkit for pdf conversion
import pdfkit
import base64
# importing logging for creating status logs 
import logging
# importing os for loading environmental variables
import os
# importing required functions from dotenv module
from dotenv import load_dotenv
import re

logger=logging.getLogger(__name__)
logging.basicConfig(filename='app.log',level=logging.INFO,format='%(asctime)s-%(levelname)s-%(message)s')

#loading variables from .env files
load_dotenv()

#replace with your own credentials 
ORGANISATION=os.getenv('ORGANISATION')
PROJECT=os.getenv('PROJECT')
WIKI_IDENITFIER=os.getenv('WIKI_IDENTIFIER')
PAT_TOKEN=os.getenv('PAT_TOKEN')
OUTPUT_FOLDER=f'Data/{WIKI_IDENITFIER}'
         
auth_string = f":{PAT_TOKEN}"
base64_auth_string = base64.b64encode(auth_string.encode()).decode()

headers = {
    'Authorization': f'Basic {base64_auth_string}',
    'Content-Type': 'application/json'
}

#fetches the pages in wiki
def get_wiki_pages():
    pages=[]
    continuation_token=None
    while True:
        url = f'https://dev.azure.com/{ORGANISATION}/{PROJECT}/_apis/wiki/wikis/{WIKI_IDENITFIER}/pages?path=/&recursionLevel=OneLevel&api-version=7.2-preview.1'
        url += f'&continuationToken={continuation_token}'
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                pages.extend(data['subPages'])
                continuation_token = data.get('continuationToken')
                if not continuation_token:
                    break
            else:
                logger.error(f'Failed to fetch wiki pages: {response.status_code}')
                break
        except Exception as e:
            logger.error(e)
    return pages 

# fetches the content of the page 
def get_page_content(page_path):
    try:
        page_url=f'https://dev.azure.com/{ORGANISATION}/{PROJECT}/_apis/wiki/wikis/{WIKI_IDENITFIER}/pages?path={page_path}&includeContent=True&api-version=7.2-preview.1'
        response=requests.get(page_url,headers=headers)
        response.raise_for_status()
        data=response.json()
        return  data['content']
    except Exception as e:
        logger.error(f'failed to load page content:{e}')

# converting extracted content to pdf file
def convert_html_to_pdf(html_content, output_filename,page_name):
    try:
        pdfkit.from_string(html_content, output_filename)
        logger.info("file %s created successfully",page_name)
    except Exception as e:
        logger.error(f'Failed to convert {output_filename} file: {e}')

def main():
    pages=get_wiki_pages()
    try:
        if not os.path.exists(OUTPUT_FOLDER): # checks and creates folder for the files
            os.makedirs(OUTPUT_FOLDER)

        logger.info('creating files')

        for page in pages:
            page_path=page['path']
            page_name=re.sub(r'[<>:"/\\|?*]', '', page_path)
            content = get_page_content(page_path)
            output_filename = os.path.join(OUTPUT_FOLDER, f"page_{page_name}.pdf")
            convert_html_to_pdf(content, output_filename,page_name)
    except Exception as e:
        logger.error(e)

if __name__=="__main__":
    main()
