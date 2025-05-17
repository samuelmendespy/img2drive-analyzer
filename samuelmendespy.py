import requests
import base64
import time
import json
import io
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environemnt variables
load_dotenv()

# Google Drive upload service configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'client_secret.json'
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# The URL of the page to be scraped
page_url = os.environ.get("SCRAP_TARGET")

# API Configuration
api_url = os.environ.get("API_URL")
auth_token = os.environ.get("AUTH_TOKEN")
model_id = "microsoft-florence-2-large"
task_prompt = "<DETAILED_CAPTION>"

# submission url
submission_url = os.environ.get("SUBMIT_ENDPOINT")

def scrap_image_bytes():
    """
    Scrap an image from the page as image bytes.

    Returns:
        bytes or None: The raw bytes of the first jpeg image found encoded or null
    """
    try:
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find("img", {"src": lambda x: x and x.startswith("data:image/jpeg;base64,")})

        if img_tag and "src" in img_tag.attrs:
            base64_data = img_tag['src'].split(",")[1]
            image_bytes = base64.b64decode(base64_data)
            return image_bytes
        else:
            print("There are no images encoded in base64 inside <img> tags..")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def obtain_input_image_url():
    """
    Upload image to Google Drive to obtain a direct image url.

    Returns:
        url (str) or None: An url string or None
    """
    # Image bytes of the input image
    image_bytes = scrap_image_bytes()

    if not image_bytes:
        print("Could not find image_bytes to upload.")
        return None
    
    try:
        # Create the media file upload object
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype='image/jpeg', resumable=True)

        # Create image file on Google Drive
        filename = "image.jpg"
        file_metadata = {'name': filename}
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        print(f"Image file with ID: '{file_id}' has been uploaded to Google Drive.")

        # Assign permission to allow anyone to access the uploaded image
        permission = {'role': 'reader', 'type': 'anyone'}
        service.permissions().create(fileId=file_id, body=permission).execute()
        
        # Format the url to acess the image
        url = f"https://drive.google.com/uc?export=view&id={file_id}"
        return url

    except Exception as error:
        print(f'An error occurred while uploading image bytes: {error}') 
        return None   

def request_inference(input_image_url, task_prompt):
    """
    Post a image as input with promt to a model perform a task.

    Args:
        input_image_url: A JPEG image URL.
        task_prompt: Prompt with task to be performed.

    Returns:
        JSON: A JSON response with inferece to the input image or None.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    data = {
        "model": model_id,
        "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": task_prompt},
                {
                    "type": "image_url",
                    "image_url": { "url": input_image_url 
                    }
                }
            ]
        }
    ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if response is not None:
            print(f"Response status code: {response.status_code}")
            try:
                error_json = response.json()
                print(f"Error details: {json.dumps(error_json, indent=2)}")
            except json.JSONDecodeError:
                print(f"Could not decode error response as JSON. Response text: {response.text}")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        return None
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return None
    except json.JSONEncodeError as e:
        print(f"Error encoding payload to JSON: {e}")
    except requests.exceptions.RequestException as req_err:
        print(f"Error while trying to request inference: {req_err}")
        return None
        if response is not None:
            print(f"Response status code: {response.status_code}")
            try:
                print(f"Response body: {response.json()}")
            except json.JSONDecodeError:
                print(f"Response body (text): {response.text}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def sumbmit_response(response_data):
    """
    Submit data to submission endpoint.

    Args:
        response_data (JSON): A JSON response resulted from request_inference(input_image_url, task_prompt).

    Returns:
        True or False: Returns true for sucess and False for failure.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    if response_data is None:
        print("Null response_data sent as parameter.")
        return False
    
    try:
        response = requests.post(submission_url, json=response_data, headers=headers)
        response.raise_for_status()
        response_json = response.json

        print("Request sucessful")
        print("Status code", response.status_code)
        return True

    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar dados: {e}")
        return False
    except json.JSONEncodeError as e:
        print(f"Error encoding payload to JSON: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    
if __name__ == '__main__':
    # Direct URL to the input image
    input_image_url = obtain_input_image_url()

    if input_image_url:
        inference_response_json = request_inference(input_image_url, task_prompt)

        if inference_response_json:
            result = sumbmit_response(inference_response_json)

            if result:
                print("The inference response was successfully submitted")