# yt-archive

YT-Archive is a Python tool that allows you to download videos from a YouTube channel and scrape comments from those videos.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [TODO](#TODO)
- [License](#license)

## Introduction

This project provides a straightforward tool for bulk downloading videos from a YouTube channel and scraping comments from those videos. Whether you want to archive videos for offline viewing or analyze the comments for research, this tool can help you automate the process.

## Features

- Download videos from a YouTube channel.
- Scrape comments from downloaded videos. (in development)
- Supports multithreading and multiprocessing for efficient downloading.
- Save metadata and comments to MongoDB or JSON files.
- Headless browsing using Selenium for web scraping.

## Requirements

- Python 3.x
- Chrome WebDriver (should be automatically installed by the tool, otherwise see https://chromedriver.chromium.org/)
- Various Python libraries (see requirements.txt)

## Installation

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/ilumn/yt-archive.git
   ```
    Install the required Python packages using pip:

    ```bash
    pip install -r requirements.txt
    ```
    
    Download and configure the Chrome WebDriver if it is not automatically installed by the tool. Make sure the WebDriver executable is in your system's PATH or in the project directory.

2. Configure the environment (see [Configuration](#configuration))

    Modify the ```.env.template``` file with your parameters and save as ```.env```

3. Run the tool (see [Usage](#usage))
    ```bash
    python main.py
    ```

## Usage

You can use this tool to download videos and scrape comments from a YouTube channel. Here are some usage examples:
Downloading Videos and Scraping Comments

```bash
python main.py --use-mongodb --processes 4
```
    --use-mongodb: Use MongoDB to track downloaded videos and cache comments.
    --processes 4: Define the number of simultaneous video downloads (default is 4, minimum 2, maximum 256).

Downloading Videos and Scraping Comments (Single-Processing)

```bash
python main.py --use-mongodb --single-processing
```
    --single-processing: Skip multiprocessing and download videos one at a time. 
                         More stable on sub-gigabit internet.

## Configuration

Before running the tool, you'll need to configure it by setting environment variables. Create a .env file and add the following variables (.env.template available):

    MONGODB_URI: MongoDB connection URI (if using MongoDB).
    MONGODB_DB: MongoDB database name (if using MongoDB).
    MONGODB_COLLECTION: MongoDB collection name (if using MongoDB).
    DOWNLOAD_FOLDER: Folder where videos will be downloaded.
    CHANNEL_URL: URL of the YouTube channel videos page (/videos at the end) you want to scrape.
    USE_TITLES_AS_FILENAMES: true/false, if false video id will be used as the filename instead

## Contributing

Contributions are encouraged. If you would like to contribute to this project, please open an issue or submit a pull request.
License

## TODO
listed in order of highest to lowest priority.
- fix comment scraping
- add age gate bypassing (for downloading age restricted or content restricted videos)
- add video description to metadata
- add command line flag to save more metadata such as the youtube channel's subscribers at the time of download, pinned comments, video advertising id/hotspots available codecs/resolutoins, etc.
- add support to use this tool (especially the comment scraper) as a library for other projects
- possible switch to concurrent futures for multithreading
- possible rewrite using pafy, yt-dl, or youtube-dl instead of pytube
- configure github application testing

## License
This project is licensed under the GNU GPLv3 License. See the LICENSE file for details.
