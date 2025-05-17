# Project
This project is a solution specific to a take-home test. It uses a python script to scrap a image from a website, upload the image to Google Drive and get image analyzed by a AI Mode ofl Vision-Langue Model(VLM).

## Script features:
- Scrap a image with BeautifulSoup.
- Convert JPEG image encoded as base64 to a image.jpg on Google Drive.
- Upload image bytes to Google Drive to create a image file.
- Make a direct url to a Google Drive image file that can be embed.
- HTTP Request to VLM microsoft-florence-2 to get image inference.
- HTPP exception handling.

## How it works
The script has 3 stages, [1]creates a URL string pointing to a image.jpg file, [2]the script sends a HTTP POST request to microsoft-florence-2, [3]the response to the request is then sent on a new POST HTTP request.


1 - Simple generating a direct image url :
The script requires image_url to be a direct image url, a url that points direct to load only the image.jpg, like opening a downlodaded image with the browser. It is easy to achieve by copying a random link to jpg image on the internet, but the project requiriment is to use a JPEG image encoded as base64 in a webpage in page_url that may dynamically change. The script will use BeautifulSoup to scrap the encoded image, extract the image bytes and upload the image bytes to Google Drive to create a file 'image.jpg', then the script formats a image_url that points direct to the image.jpg.

2 - Sending a image to inference by microsoft-florence-2:
With the image_url, possible to send a POST HTTP request to the model. Sample POST request bellow:

```
headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

data = {
    "model": "microsoft-florence-2",
    "messages": [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "<DETAILED CAPTION>"},
            {
                "type": "image_url",
                "image_url": { "url": "localhost:8080/image.jpg" 
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
```


3 - Forwarding response:
The script sends the POST HTTP request to the model(2) and returns the response.json, it is the JSON Body of the request and is used to send another POST request with same headers, but to a specific submission_url. Sample request bellow:
```
headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

try:
    response = requests.post(submission_url, json=response_data, headers=headers)
    response.raise_for_status()
    response_json = response.json
```


## Requiriments to use Google Drive API services
Obtain your client_secret.json(Service Account credential) to 

1 - Go to https://console.developers.google.com/

2 - Create a project, Enable API -> Select Drive API and Enable.

3 - Create Service account and Grant acess to project with role Actions Admin.

4 - Go to Services Account - Select the account to open it.

5 - Go to Keys -> Add key -> Key type", select JSON.

6 - Click Create and the download of your client secret JSON file will start.

7 - Rename the JSON file to client_secret.json