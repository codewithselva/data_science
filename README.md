Youtube Data Harvesting
This Python script allows you to extract, transform, and load data from YouTube using the YouTube API. The data is then stored in a MongoDB database and further transformed and loaded into a MySQL database.

Prerequisites
Before running the script, make sure you have the following installed:

Python
Google API Python Client
Streamlit
Pymongo
MySQL Connector
Pandas
Additionally, you need to obtain a YouTube API key and provide it in the script.

Getting Started
Clone the repository:

bash
Copy code
git clone https://github.com/yourusername/your-repository.git
Install the required dependencies:

bash
Copy code
pip install -r requirements.txt
Set up MongoDB:

Make sure you have MongoDB installed and running on your local machine.
The script assumes a MongoDB database named "youtube" with a collection named "channelDetails."
Set up MySQL:

Make sure you have MySQL installed and running on your local machine.
The script assumes a MySQL database named "youtube_harvesting" with tables named "CHANNEL," "PLAYLIST," "VIDEOS," and "COMMENT."
Replace the placeholder values in the script:

Replace the placeholder values for the YouTube API key (youtube_api_key) and other database connection details.
Run the script:

bash
Copy code
streamlit run your_script_name.py
Usage
Enter the YouTube channel ID in the provided input box.
Click the "Extract" button to fetch data from the YouTube API and store it in MongoDB.
Click the "Transform data" button to load the transformed data into the MySQL database.
View the transformed data using Streamlit's user interface.
Note
Make sure to handle API key and database connection details securely.
This script assumes local installations of MongoDB and MySQL. Adjust connection details accordingly for remote databases.
Disclaimer
This script is provided as-is and may require modifications based on your specific use case or changes in the YouTube API.

Disclaimer: Replace "yourusername" and "your-repository" with your GitHub username and repository name. Update the script name accordingly.
