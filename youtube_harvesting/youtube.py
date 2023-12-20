from googleapiclient.discovery import build
import streamlit as st
from pymongo.mongo_client import MongoClient
import mysql.connector
import pandas as pd
from datetime import datetime

def connect_to_api(service_name, version, key):
    api = build(service_name, version, developerKey=key)
    return api

key = 'AIzaSyCDKVBE1feDfh-scQv2wibBFN796Uzls5E'
service_name = 'youtube'
version = 'v3'
youtube_api = connect_to_api( service_name,version, key  )

def fetch_channel_info(channel_id):
    try:
        request = youtube_api.channels().list(part="snippet, ContentDetails, statistics, status",id=channel_id)
        response = request.execute()
        for i in response['items']:
            print("channel information: ",i)
            data = dict(Channel_Name = i["snippet"]["title"], 
                    Channel_Id=i["id"], 
                    Subscription_Count=i['statistics']['subscriberCount'],
                    Channel_Views = i['statistics']['viewCount'],
                    Channel_Type = i['kind'].split('#')[-1],
                    Channel_Status = i['status']['privacyStatus'],
                    Channel_Total_videos = i['statistics']['videoCount'] ,
                    Channel_Description = i['snippet']['description'],
                    Playlist_Id = i['contentDetails']['relatedPlaylists']['uploads']
                    )
    except Exception as e:
        raise Exception(e) 
    return data

def extract_video_ids(channel_id):
    try:
        video_ids = []
        playlist_request = youtube_api.channels().list(id = channel_id, #channel_id
                                            part ="contentDetails") 
        playlist_response = playlist_request.execute()
        playlist_id = playlist_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        next_page_token =  None

        while True:
            playlist_item_request = youtube_api.playlistItems().list(part="snippet", 
                                                                playlistId=playlist_id,
                                                                maxResults = 50,
                                                                pageToken = next_page_token)
            playlist_item_response = playlist_item_request.execute()

            for i in range (len(playlist_item_response['items'])):
                video_ids.append(playlist_item_response['items'][i]['snippet']['resourceId']['videoId'])
            next_page_token = playlist_item_response.get('nextPageToken')
            if not next_page_token:
                break
    except Exception as e:
        raise Exception(e) 
    return video_ids

def extract_video_details(video_ids):
    try:
        video_data_list = []
        for video_id in video_ids:
            video_request = youtube_api.videos().list(
                part = 'snippet, contentDetails, statistics',
                id = video_id
            )
            video_response = video_request.execute()

            for item in video_response['items']:
                #print("video_detail : ", item)
                data = dict(#Channel_Name = item['snippet']['channelTitle'],
                            #Channel_Id = item['snippet']['channelId'],
                            Video_Id = item['id'],
                            Video_Name = item['snippet']['title'],
                            Tags = item['snippet'].get('tags'),
                            Thumbnail = item['snippet']['thumbnails']['default']['url'],
                            Video_Description = item['snippet'].get('description'),
                            PublishedAt=item['snippet']['publishedAt'],
                            Duration = item['contentDetails']['duration'],
                            View_Count = item['statistics'].get('viewCount'),
                            Like_Count = item['statistics'].get('likeCount') , #check here
                            Dislike_Count = item['statistics'].get('dislikeCount') , #check here
                            Comment_Count = item['statistics'].get('commentCount'),
                            Favorite_Count = item['statistics']['favoriteCount'],
                            #video_definition_type = item['contentDetails']['definition'],
                            Caption_Status = item['contentDetails']['caption']
                            )
                video_data_list.append(data)
    except Exception as e:
        raise Exception(e)
    return video_data_list

def extract_comments_details(video_ids):
    try:
        comments_list = []
        for video_id in video_ids:
            comments_request = youtube_api.commentThreads().list(
                part = 'snippet',
                videoId = video_id,
                maxResults = 50
            )
            comments_response = comments_request.execute()
            for item in comments_response['items']:
                data = dict(Comment_Id = item['snippet']['topLevelComment']['id'],
                            Video_Id = item['snippet']['topLevelComment']['snippet']['videoId'],
                            Comment_Text = item['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_Author = item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_PublishedAt = item['snippet']['topLevelComment']['snippet']['publishedAt']                    
                            )
                comments_list.append(data)
    except Exception as e:
        raise Exception(e) 
    return comments_list

def extract_playlist_details(channel_id):
    next_page_token = None
    playlist_details = []
    try:
        while True:
            playlist_request = youtube_api.playlists().list(
                part = 'snippet, contentDetails',
                channelId = channel_id,
                maxResults = 50,
                pageToken = next_page_token
            )

            playlist_response = playlist_request.execute()

            for playlist in playlist_response['items']:
                #print("playlist1 : ", playlist)
                data = dict(
                    playlist_id = playlist['id'],
                    playlist_title = playlist['snippet']['title'],
                    channel_id = playlist['snippet']['channelId'],
                    channel_name = playlist['snippet']['channelTitle'],
                    published_at = playlist['snippet']['publishedAt'],
                    playlist_video_count = playlist['contentDetails']['itemCount'],
                )
                playlist_details.append(data)
            next_page_token = playlist.get('nextPageToken')
            if not next_page_token:
                break
    except Exception as e:
        raise Exception(e)
    return playlist_details

def build_channel_details(channel_id):
    try:
        channel_details = fetch_channel_info(channel_id)
        playlist_details = extract_playlist_details(channel_id)
        video_ids = extract_video_ids(channel_id)
        video_details = extract_video_details(video_ids)
        comments_details = extract_comments_details(video_ids)
        collectionChannel = db["channelDetails"]
        collectionChannel.insert_one({"channel_information":channel_details, 
                                    "playlist_information":playlist_details,
                                    "video_information":video_details,
                                    "comment_information":comments_details
                                    })
    except Exception as e:
        raise Exception(e)
    return "Channel Information saved to Mongodb!"

def load_channel_data_to_SQL(channel_id):
    channelList = []
    db = client["youtube"]
    channelDetails = db["channelDetails"]
    for channel in channelDetails.find({"channel_information.Channel_Id":channel_id},{"_id":0,"channel_information":1}):
        channelList.append(channel["channel_information"])
    channelDataFrame = pd.DataFrame(channelList)
    for index, row in channelDataFrame.iterrows():
        insert_query='''INSERT INTO CHANNEL(
                                        CHANNEL_ID,
                                        CHANNEL_NAME,
                                        CHANNEL_DESCRIPTION,
                                        CHANNEL_STATUS,
                                        CHANNEL_TYPE,
                                        CHANNEL_VIEWS,
                                        channel_video_count)
                        VALUES( %s,%s,%s,%s,%s,%s,%s)'''
        values = (row['Channel_Id'],
                row['Channel_Name'],
                row['Channel_Description'],
                row['Channel_Status'],
                row['Channel_Type'],
                row['Channel_Views'],
                row['Channel_Total_videos'])
        try:
            mycursor.execute(insert_query,values)
            mydb.commit()
        except Exception as e:
            print(row['Channel_Id'],e)
            raise Exception(e)
    return "Channel information saved successfully!"

def load_playlist_data_to_SQL(channel_id):
    playLists = []
    playlistDetails = db["channelDetails"]

    for playList in playlistDetails.find({"channel_information.Channel_Id":channel_id},{"_id":0,"playlist_information":1}):
        for play in playList['playlist_information']:
            playLists.append(play)
    playlistDataFrame = pd.DataFrame(playLists)
    for index, row in playlistDataFrame.iterrows():
        playlist_id = row.get('playlist_id')
        channel_id = row.get('channel_id')
        playlist_title = row.get('playlist_title')
        if playlist_id is None or channel_id is None or playlist_title is None:
            print(f"Skipping row {index} due to missing values.")
            continue
        insert_query='''INSERT INTO PLAYLIST(
                                        PLAYLIST_ID,
                                        CHANNEL_ID,
                                        PLAYLIST_NAME)
                        VALUES( %s,%s,%s)'''
        values = (playlist_id,channel_id,playlist_title)
        try:
            mycursor.execute(insert_query,values)
            mydb.commit()
        except Exception as e:
            print(row.get('playlist_id'),e)
            raise Exception(e)
    return "Playlist information saved successfully!"

def load_video_data_to_SQL(channel_id):
    videoList = []
    videoDetails = db["channelDetails"]

    for videos in videoDetails.find({"channel_information.Channel_Id":channel_id},{"_id":0,"video_information":1}):
        #print(videos)
        for video in videos['video_information']:
            #print(video)
            videoList.append(video)
    videoDataFrame = pd.DataFrame(videoList)
    for index, row in videoDataFrame.iterrows():
        #print(index)
        #print(row)
        video_id=row.get('Video_Id')
        #playlist_id=row.get('Playlist_Id','PLJYf0JdTApCoAWBCGq1CBysA6Tx3ALIcQ')
        playlist_id='PLRCiS0r_uoCEytZb1L53tZbOw5L6PIKXk'
        video_name=row.get('Video_Name')
        video_description=row.get('Video_Description')
        input_datetime = datetime.strptime(row.get('PublishedAt'), '%Y-%m-%dT%H:%M:%SZ')
        published_date = input_datetime.strftime('%Y-%m-%d %H:%M:%S')
        #print("View count ",row.get('View_Count'))
        view_count=row.get('View_Count',0)
        like_count=row.get('Like_Count',0)
        dislike_count=row.get('Dislike_Count',0)
        favorite_count=row.get('Favorite_Count',0)
        comment_count=row.get('Comment_Count',0)
        # Extract minutes and seconds from the input string
        #print("Duration : ",row.get('Duration'))
        minutes = 0
        seconds = 0
        duration_str = row.get('Duration')
        if 'M' in duration_str:
            minutes_index = duration_str.index('M')
            minutes = int(duration_str[2:minutes_index])

        if 'S' in duration_str:
            seconds_index = duration_str.index('S')
            seconds_str = duration_str[minutes_index + 1:seconds_index]
            seconds = int(seconds_str) if seconds_str else 0

        # Calculate total duration in seconds
        total_seconds = minutes * 60 + seconds
        # Create a timedelta object
        duration=total_seconds

        thumbnail=row['Thumbnail']
        caption_status=row.get('Caption_Status')

        insert_query='''INSERT INTO VIDEOS(
                                        video_id,
                                        playlist_id,
                                        video_name,
                                        video_description,
                                        published_date,
                                        view_count,
                                        like_count,
                                        dislike_count,
                                        favorite_count,
                                        comment_count,
                                        duration,
                                        thumbnail,
                                        caption_status)
                        VALUES( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        values = (video_id,
                                        playlist_id,
                                        video_name,
                                        video_description,
                                        published_date,
                                        view_count,
                                        like_count,
                                        dislike_count,
                                        favorite_count,
                                        comment_count,
                                        duration,
                                        thumbnail,
                                        caption_status)

        try:
            mycursor.execute(insert_query,values)
            mydb.commit()
        except Exception as e:
            print(video_id,e)
            raise Exception(e)
    return "Video information saved successfully!"

def load_comments_data_to_SQL(channel_id):
    result=[]
    commentList = []
    commentDetails = db["channelDetails"]

    for comments in commentDetails.find({"channel_information.Channel_Id":channel_id},{"_id":0,"comment_information":1}):
        #print(videos)
        for comment in comments['comment_information']:
            #print(comment)
            commentList.append(comment)
    commentDataFrame = pd.DataFrame(commentList)


    for index, row in commentDataFrame.iterrows():
        #print(index)
        print(row)
        video_id=row.get('Video_Id')
        comment_id=row.get('Comment_Id')
        comment_text=row.get('Comment_Text')
        comment_author=row.get('Comment_Author')
        input_datetime = datetime.strptime(row.get('Comment_PublishedAt'), '%Y-%m-%dT%H:%M:%SZ')
        comment_published_date = input_datetime.strftime('%Y-%m-%d %H:%M:%S')

        insert_query='''INSERT INTO COMMENT(
                                        comment_id,
                                        video_id,
                                        comment_text,
                                        comment_author,
                                        comment_published_date)
                        VALUES( %s,%s,%s,%s,%s)'''
        values = (comment_id,
                                        video_id,
                                        comment_text,
                                        comment_author,
                                        comment_published_date)
        
        try:
            mycursor.execute(insert_query,values)
            mydb.commit()
        except Exception as e:
            print(comment_id,e)
            raise Exception(e)
    return "Comments information saved successfully!"


def show_channels_table():
    channelList = []
    channelDetails = db["channelDetails"]

    for channel in channelDetails.find({},{"_id":0,"channel_information":1}):
        channelList.append(channel["channel_information"])
    return st.dataframe(channelList)

def show_playlist_table():
    playLists = []
    playlistDetails = db["channelDetails"]

    for playList in playlistDetails.find({},{"_id":0,"playlist_information":1}):
        #print(playList)
        for play in playList['playlist_information']:
            #print(play)
            playLists.append(play)
    return st.dataframe(playLists)

def show_video_table():    
    videoList = []
    videoDetails = db["channelDetails"]

    for videos in videoDetails.find({},{"_id":0,"video_information":1}):
        #print(videos)
        for video in videos['video_information']:
            #print(video)
            videoList.append(video)
    return st.dataframe(videoList)

def show_comments_table():  
    commentList = []
    commentDetails = db["channelDetails"]

    for comments in commentDetails.find({},{"_id":0,"comment_information":1}):
        #print(videos)
        for comment in comments['comment_information']:
            #print(comment)
            commentList.append(comment)
    return st.dataframe(commentList)



client = MongoClient("mongodb://localhost:27017")
db = client["youtube"]
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="password",
  database='youtube_harvesting'
)
mycursor = mydb.cursor(buffered=True)


#Streamlit code

st.title(":blue[Youtube Data Harvesting]")
st.header("Extract data from Youtube")
channel_id = st.text_input("Enter the channel ID")
print("channel_id:", channel_id)
if not channel_id:
    st.warning("Please enter a valid Channel ID.")
else:
    if st.button("Extract"):
        ch_ids =[]
        channelCollection = db["channelDetails"]
        for ch_data in  channelCollection.find({},{"_id":0,"channel_information":1}):
            ch_ids.append(ch_data['channel_information']['Channel_Id'])
        if channel_id in ch_ids:
            st.success("Channel details exists already")
        else:
            with st.spinner("Extracting data..."):
                try:
                    result = build_channel_details(channel_id)
                    st.success(result)
                except Exception as e:
                    print(e)
                    st.warning("Exception Occurred! Please try again after sometime.")
if st.button("Transform data"):
    try:
        load_channel_data_to_SQL(channel_id)
        load_playlist_data_to_SQL(channel_id)
        load_video_data_to_SQL(channel_id)
        load_comments_data_to_SQL(channel_id)
    except Exception as e:
        print(e)
        st.warning("Exception Occurred! Please try again after sometime.")
st.markdown("<hr>", unsafe_allow_html=True)        
st.header("View Transformed Data")
show_table = st.radio("Select Table",("Channel", "Playlist","Videos","Comments"))
if show_table=="Channel":
    show_channels_table()
elif show_table =='Playlist':
    show_playlist_table()
elif show_table=='Videos':
    show_video_table()
elif show_table=='Comments':
    show_comments_table()

st.markdown("<hr>", unsafe_allow_html=True)
#SQL COnnection
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="password",
  database='youtube_harvesting'
)
mycursor = mydb.cursor(buffered=True)
mycursor.execute("SELECT * FROM youtube_harvesting.questions order by id")
result = mycursor.fetchall()
question_dict = []
query_dict = []
for record in result:
    question_dict.append({"name":record[1], "id":record[0]})
    query_dict.append({"id":record[0], "query":record[2]})

# Use the keys of question_dict to create a list for the selectbox
question_names = [item["name"] for item in question_dict]
st.header("View Analyzed Data")
# Create a Streamlit selectbox
selected_question = st.selectbox("Choose a question", question_names)

# Get the corresponding ID and query based on the selected question
selected_question_id = next(item["id"] for item in question_dict if item["name"] == selected_question)
selected_query = next(item["query"] for item in query_dict if item["id"] == selected_question_id)

mycursor.execute(selected_query)
result = mycursor.fetchall()
# Get column names from the cursor description
column_names = [desc[0] for desc in mycursor.description]
dataFrame = pd.DataFrame(result, columns=column_names)
st.write(dataFrame) 