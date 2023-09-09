# based on https://github.com/egbertbouman/youtube-comment-downloader

import requests
import json
import time
import re

def search_dict(partial, key):
    if isinstance(partial, dict):
        for k, v in partial.items():
            if k == key:
                yield v
            else:
                for o in search_dict(v, key):
                    yield o
    elif isinstance(partial, list):
        for i in partial:
            for o in search_dict(i, key):
                yield o

def find_value(html, key, num_sep_chars=2, separator='"'):
    start_pos = html.find(key) + len(key) + num_sep_chars
    end_pos = html.find(separator, start_pos)
    return html[start_pos:end_pos]

def get_comments(url, limit=None):
    session = requests.Session()
    res = session.get(url)
    xsrf_token = find_value(res.text, "XSRF_TOKEN", num_sep_chars=3)
    data_str = find_value(res.text, 'window["ytInitialData"] = ', num_sep_chars=0, separator="\n").rstrip(";")
    data = json.loads(data_str)

    for r in search_dict(data, "itemSectionRenderer"):
        pagination_data = next(search_dict(r, "nextContinuationData"), None)
        if pagination_data:
            break

    continuation_tokens = [(pagination_data['continuation'], pagination_data['clickTrackingParams'])]

    while continuation_tokens:
        continuation, itct = continuation_tokens.pop()
        params = {
            "action_get_comments": 1,
            "pbj": 1,
            "ctoken": continuation,
            "continuation": continuation,
            "itct": itct,
        }
        data = {
            "session_token": xsrf_token,
        }
        headers = {
            "x-youtube-client-name": "1",
            "x-youtube-client-version": "2.20200731.02.01"
        }
        response = session.post("https://www.youtube.com/comment_service_ajax", params=params, data=data, headers=headers)
        comments_data = json.loads(response.text)

        for comment in search_dict(comments_data, "commentRenderer"):
            yield {
                "commentId": comment["commentId"],
                "text": ''.join([c['text'] for c in comment['contentText']['runs']]),
                "time": comment['publishedTimeText']['runs'][0]['text'],
                "isLiked": comment["isLiked"],
                "likeCount": comment["likeCount"],
                "replyCount": comment["replyCount"],
                'author': comment.get('authorText', {}).get('simpleText', ''),
                'channel': comment['authorEndpoint']['browseEndpoint']['browseId'],
                'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                'photo': comment['authorThumbnail']['thumbnails'][-1]['url'],
                "authorIsChannelOwner": comment["authorIsChannelOwner"],
            }

        continuation_tokens = [(next_cdata['continuation'], next_cdata['clickTrackingParams'])
                         for next_cdata in search_dict(comments_data, 'nextContinuationData')] + continuation_tokens

        time.sleep(0.1)

def get_comments_v2(video_url):
    try:
            # Make a GET request to the YouTube video URL
        response = requests.get(video_url)
        response.raise_for_status()

        # Search for the JSON data containing comments using a regular expression
        match = re.search(r'window\["ytInitialData"\] = ({.*?});', response.text, re.DOTALL)
        if match:
            data_str = match.group(1)

            # Parse the JSON data
            data = json.loads(data_str)

            # Extract comments data
            if "contents" in data:
                comments_data = data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1]["commentThreadRenderer"]["commentThreadingRenderer"]["commentRenderer"]
                for comment_info in comments_data:
                    yield comment_info
            else:
                print("No comments data found in JSON.")
        else:
            print("JSON data not found on the page.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")