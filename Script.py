import os
import json
import requests
import datetime
import csv
from unidecode import unidecode

# CHANGE THESE SETTINGS!
saveDirectory = './'  # Replit working directory
boardLetter = 'g'  # Example board: 'hum' for human

print("The current working directory is " + saveDirectory)

# Create a folder for the board.
path = os.path.join(saveDirectory, boardLetter)
print(f"Attempting to create directory for board at {path}")
try:
    os.mkdir(path)
except OSError:
    print(f"Creation of the directory {path} failed - possible directory already exists")
else:
    print(f"Successfully created the directory {path}")

# Get the 4chan board catalog JSON file
url = f"https://a.4cdn.org/{boardLetter}/catalog.json"
response = requests.get(url)

# Check if the response is valid
if response.status_code != 200:
    print(f"Failed to retrieve catalog. Status code: {response.status_code}")
    exit()

threadCatalog = response.json()

print("BEGINNING 4CHAN FRONT PAGE SCRAPE")
print("Current board: " + boardLetter)

downloadCounter = 0

# Only look at the front page
frontPage = threadCatalog[0]['threads']

# Create a file to list all threads we've analyzed
allThreadFile = os.path.join(saveDirectory, boardLetter, f"frontPage-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
with open(allThreadFile, mode='w', newline='', encoding='utf-8') as thread_file:
    thread_writer = csv.writer(thread_file)
    thread_writer.writerow(["timeStamp", "lastScraped", "posterID", "name", "postID", "subjectText", "commentText"])

print("Now parsing front page threads...")
# Loop through and read each thread
for i in range(len(frontPage)):
    print("STARTING NEW THREAD - #" + str(frontPage[i]['no']))

    # Failsafes for missing information
    subjectText = frontPage[i].get('sub', "No Subject Text Provided")
    commentText = frontPage[i].get('com', "No Comment Text Provided")

    with open(allThreadFile, mode='a', newline='', encoding='utf-8') as thread_file:
        thread_writer = csv.writer(thread_file)
        thread_writer.writerow([
            frontPage[i]['now'],
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            frontPage[i].get('id', "No ID"),
            frontPage[i]['name'],
            frontPage[i]['no'],
            subjectText,
            commentText
        ])

    # Create a new directory for the thread
    thread_path = os.path.join(saveDirectory, boardLetter, f"{frontPage[i]['no']} - {frontPage[i]['semantic_url']}")
    print(f"Attempting to create directory for thread {thread_path}")
    try:
        os.mkdir(thread_path)
    except OSError:
        print(f"Creation of the directory {thread_path} failed - possible directory already exists")

    # Create a CSV File for the individual thread
    thread_csv_file = os.path.join(thread_path, "thread.csv")
    with open(thread_csv_file, mode='w', newline='', encoding='utf-8') as thread_file:
        thread_writer = csv.writer(thread_file)
        thread_writer.writerow(["timeStamp", "posterID", "name", "postID", "subjectText", "commentText", "filename"])

    # Get the individual thread JSON file from 4chan
    thread_url = f"https://a.4cdn.org/{boardLetter}/thread/{frontPage[i]['no']}.json"
    thread_response = requests.get(thread_url)

    if thread_response.status_code != 200:
        print(f"Failed to retrieve thread {frontPage[i]['no']}. Status code: {thread_response.status_code}")
        continue

    individualThread = thread_response.json()

    # Loop through every post in this thread
    for post in individualThread['posts']:
        print("Now processing post " + str(post['no']))
        timeStamp = post['now']
        name = post.get('name', 'Anonymous')
        posterID = post.get('id', "No ID")
        postID = post['no']
        subjectText = post.get('sub', "No Subject Text Provided")
        commentText = post.get('com', "No Comment Text Provided")

        # Check for images
        if 'tim' in post:
            original_filename = unidecode(post.get('filename', ''))
            renamed_file = str(post['tim'])
            file_extension = str(post['ext'])
            filename = f"{original_filename} - {renamed_file}{file_extension}"
            image_url = f"https://i.4cdn.org/{boardLetter}/{renamed_file}{file_extension}"

            # Save the image
            image_path = os.path.join(thread_path, filename)
            try:
                img_response = requests.get(image_url)
                with open(image_path, 'wb') as img_file:
                    img_file.write(img_response.content)
                downloadCounter += 1
            except Exception as e:
                print(f"File Download Error: {e}")
                filename = filename + " - Download Error"
        else:
            filename = "No File Posted"

        # Write post data to the thread CSV
        with open(thread_csv_file, mode='a', newline='', encoding='utf-8') as thread_file:
            thread_writer = csv.writer(thread_file)
            thread_writer.writerow([timeStamp, posterID, name, postID, subjectText, commentText, filename])

print("Front Page Scrape Completed - " + str(downloadCounter) + " files downloaded")
