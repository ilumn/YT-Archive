import os
import re
import json
import time
import argparse
import requests
import wget
import zipfile
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from pytube import YouTube
from pytube.cli import on_progress
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from multiprocessing import Pool, Manager, Lock
from concurrent.futures import ThreadPoolExecutor
from youtube_comment_scraper import get_comments

def install_chrome_webdriver_latest():
    # credit https://stackoverflow.com/a/62023168 for this function
    # get the latest chrome driver version number
    if Path(os.path.join(os.getcwd(),"chromedriver.exe")).exists():
        pass
    else:
        url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
        response = requests.get(url)
        version_number = response.text

        # build the donwload url
        download_url = "https://chromedriver.storage.googleapis.com/" + version_number +"/chromedriver_win32.zip"

        # download the zip file using the url built above
        latest_driver_zip = wget.download(download_url,'chromedriver.zip')

        # extract the zip file
        with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
            zip_ref.extractall() # you can specify the destination folder path here
        # delete the zip file downloaded above
        os.remove(latest_driver_zip)
    os.environ["webdriver.chrome.driver"] = os.path.join(os.getcwd(),"chromedriver.exe")

# Load environment variables from .env file
load_dotenv()

# Get MongoDB credentials from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER")
CHANNEL_URL = os.getenv("CHANNEL_URL")

# Function to load metadata from a file
def load_metadata_from_file(metadata_file):
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as file:
            metadata = json.load(file)
        return metadata
    else:
        return {}

# Function to save metadata to a file
def save_metadata_to_file(metadata, metadata_file):
    metadata = dict(metadata)
    with open(metadata_file, 'w') as file:
        json.dump(metadata, file, indent=4)

# Function to load metadata from MongoDB
def load_metadata_from_mongodb():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]
    metadata = {}
    for record in collection.find():
        metadata[record['video_hash']] = record
    client.close()
    return metadata

# Function to save metadata to MongoDB
def save_metadata_to_mongodb(metadata):
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]
    collection.drop()  # Clear existing data
    for video_hash, data in metadata.items():
        collection.insert_one(data)
    client.close()

# Function to fetch and cache comments
def cache_comments(yt, metadata, video_hash, use_mongodb, download_folder, limit=100):
    print("a")
    comments = get_comments(yt.watch_url, limit=limit)
    print("nb")
    if not use_mongodb:
        comments_file = os.path.join(download_folder, f"{yt.title}_comments.txt")
        comments_data = []
    print("getting comment data")
    print(comments)
    for comment in comments:
        comment_info = {
            'commentId': comment["commentId"],
            'text': comment["text"],
            'time': comment["time"],
            'isLiked': comment["isLiked"],
            'likeCount': comment["likeCount"],
            'replyCount': comment["replyCount"],
            'author': comment["author"],
            'channel': comment["channel"],
            'votes': comment["votes"],
            'photo': comment["photo"],
            'authorIsChannelOwner': comment["authorIsChannelOwner"],
        }
        print("saving comment data")
        if use_mongodb:
            metadata[video_hash].setdefault('comments', []).append(comment_info)
        else:
            comments_data.append(comment_info)

    if not use_mongodb:
        print("dumping to file")
        with open(comments_file, 'w') as file:
            json.dump(comments_data, file, ensure_ascii=False, indent=4)
    
    return metadata

# Function to get video URLs from a YouTube channel page
def get_videos_in_channel(channel_url):
    # NOTE: IF ANYONE WANTS TO RETHINK HOW THIS FUNCTION IS WRITTEN BECAUSE ITS HONESTLY KIND OF MEH, I RECOMMEND USING THE ytInitialData VARIABLE IN THE PAGE, IT CONTAINS THE VIDEO IDs
    try:
        # Initialize the WebDriver with the path to the executable
        install_chrome_webdriver_latest()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options)


        # Open the channel URL
        driver.get(channel_url)

        # Scroll down to load more videos (you can adjust the number of scrolls)
        num_scrolls = 1
        init = 0
        scrolling = True
        while scrolling:
            time.sleep(5)
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            curr = driver.find_elements(By.ID, 'video-title-link').__len__()
            print(f"indexed {curr} videos")
            if curr == init:
                scrolling = False
            else:
                num_scrolls +=1
                init = curr




        # Find all video links on the channel page
        video_urls = []
        for link in driver.find_elements(By.TAG_NAME, 'a') and driver.find_elements(By.ID, 'video-title-link'):
            href = link.get_attribute('href')
            if href and "/watch?v=" in href:
                video_urls.append(href)
        print(f'{video_urls.__len__()} Videos found, {num_scrolls} Scrolls used')
        return video_urls

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

    finally:
        # Close the WebDriver
        driver.quit()


# Function to download YouTube videos
def download_videos(channel_url, download_folder, use_mongodb, metadata_file):
    if use_mongodb:
        metadata = load_metadata_from_mongodb()
    else:
        metadata = load_metadata_from_file(metadata_file)
    
    video_urls = get_videos_in_channel(channel_url)
    
    # Iterate through videos in the channel
    for video_url in video_urls:
        # print(video_url) debugging
        try:
            yt = YouTube(video_url, on_progress_callback=on_progress)
            
            # IDK if this actually bypassed the age restricion or "unsuitable content" flags but I put it here in case it does
            if yt.age_restricted:
                yt.bypass_age_gate()
            
            # print(yt.vid_info) 

            # yes ik its not actually the file hash
            video_hash = yt.video_id
            
            if video_hash not in metadata:
                stream = yt.streams.get_highest_resolution()
                stream.download(download_folder, filename=str(yt.title).replace("/","|"),)
                metadata[video_hash] = {
                    'video_url': video_url,
                    'downloaded_at': str(datetime.now()),  # Add timestamp
                    'title': yt.title,
                    'view_count': yt.views,
                    'like_count': int(re.search(r'[0-9]{1,3},?[0-9]{0,3},?[0-9]{0,3} like', str(yt.initial_data)).group(0).split(' ')[0].replace(',', '')),
                    'upload_date': yt.publish_date.strftime('%Y-%m-%d'),  # Format the date
                }
                if use_mongodb:
                    metadata[video_hash].setdefault('other_stats', []).append(yt.vid_info)
                print(f"Downloaded: {yt.title} | {video_url}")
                
                # Cache comments
                # metadata = cache_comments(yt, metadata, video_hash, use_mongodb, download_folder)
            else:
                print(f"Skipped (already downloaded): {video_url}")
        except Exception as e:
            print(f"Error downloading {video_url}: {str(e)}")
    
    if use_mongodb:
        save_metadata_to_mongodb(metadata)
    else:
        save_metadata_to_file(metadata, metadata_file)

# Function to download a single video
def download_single_video(video_url, download_folder, use_mongodb, metadata_shared):
    try:
        yt = YouTube(video_url, on_progress_callback=on_progress)
        
        if yt.age_restricted:
            yt.bypass_age_gate()
        
        # yes ik its not actually the file hash
        video_hash = yt.video_id
        
        # with lock:
        if video_hash not in metadata_shared:
            stream = yt.streams.get_highest_resolution()
            stream.download(download_folder, filename=str(yt.title).replace("/","|"))
            metadata_shared[video_hash] = {
                'video_url': video_url,
                'downloaded_at': str(datetime.now()),
                'title': yt.title,
                'view_count': yt.views,
                    'like_count': int(re.search(r'[0-9]{1,3},?[0-9]{0,3},?[0-9]{0,3} like', str(yt.initial_data)).group(0).split(' ')[0].replace(',', '')),
                'upload_date': yt.publish_date.strftime('%Y-%m-%d'),
            }
            if use_mongodb:
                metadata = metadata[video_hash].setdefault('other_stats', []).append(yt.vid_info)
            print(f"Downloaded: {yt.title} | {video_url}")
            
            # metadata = cache_comments(yt, metadata_shared, video_hash, use_mongodb, download_folder)
        else:
            print(f"Skipped (already downloaded): {video_url}")
    except Exception as e:
        print(f"Error downloading {video_url}: {str(e)}")


# Function to download videos using multiprocessing
# WARNING: THIS MIGHT CAUSE SIGNIFICANT STRAIN ON YOUR SYSTEM OR NETWORK
def download_videos_multi(download_folder, use_mongodb, processes, metadata_file):
    video_urls = get_videos_in_channel(channel_url) 
    with Manager() as manager:
        metadata_shared = manager.dict()
        

        # Load existing metadata
        if use_mongodb:
            metadata_shared.update(load_metadata_from_mongodb())
        
        else:
            metadata_shared.update(load_metadata_from_file(metadata_file))
        
        
        with Pool(processes=processes) as pool:  # Adjust the number of processes as needed
            pool.starmap(download_single_video, [(url, download_folder, use_mongodb, metadata_shared) for url in video_urls])
        
        # Save metadata
        if use_mongodb:
            save_metadata_to_mongodb(metadata_shared)
        else:
            save_metadata_to_file(metadata_shared, metadata_file)


# # # # # # # # # # # # #            
# uses concurrent.futures for download multithreading. currently not used but might switch to this if it shows to be faster.
# # # # # # # # # # # # #
def DVM_CCF(video_urls, download_folder, use_mongodb, metadata_file, num_processes):
    with Manager() as manager:
        metadata_shared = manager.dict()
        lock = manager.Lock()
        
        # Load existing metadata
        if not use_mongodb:
            metadata_shared.update(load_metadata_from_file(metadata_file))
        
        with ThreadPoolExecutor(max_workers=num_processes) as executor:  # Use ThreadPoolExecutor
            futures = []
            for url in video_urls:
                future = executor.submit(download_video, url, download_folder, use_mongodb, metadata_shared, lock)
                futures.append(future)
            
            # Wait for all futures to complete
            for future in futures:
                future.result()
        
        # Save metadata to JSON file
        save_metadata_to_file(metadata_shared, metadata_file)
# # # # # # # # # # # # #
# # # # # # # # # # # # #


# Add command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--use-mongodb', action='store_true', help='Use MongoDB to track downloaded videos and cache comments')
parser.add_argument('--processes', type=int, default=4, choices=range(2, 257), help='Define the number of simultaneous video downloads (default: 4, min: 2, max: 256)')
parser.add_argument('--single-processing', action='store_true', help='Do not use any multithreading or multiprocessing, and download videos one at a time. Note: this gentler on low end computers and slow internet connections/low bandwidth')
args = parser.parse_args()

if __name__ == "__main__":
    channel_url = CHANNEL_URL
    download_folder = DOWNLOAD_FOLDER
    metadata_file = os.path.join(download_folder,"metadata.json")

    if args.single_processing:
        print("SKIPPING MULTIPROCESSING")
        download_videos(channel_url, download_folder, args.use_mongodb, metadata_file)
    else:
        print(f"RUNNING WITH MULTIPROCESSING SET TO {args.processes}")
        download_videos_multi(download_folder, args.use_mongodb, args.processes, metadata_file)

