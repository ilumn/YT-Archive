import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import os
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

BASE_URL = "https://www.youtube.com/watch?v="
URL_PARAM = "watch?v="
URL_CHANNEL = "/channel/"
SUCCESS = "success"


def check_like_score(value):
    if value is not None:
        try:
            res = int(value)
            if not isinstance(res, int):
                return res
        except ValueError:
            pass
    return 0


def comments(url):
    if not url.startswith(('https://', 'http://')):
        id = url
        url = BASE_URL + url
    else:
        sp = url.split("/")
        id = sp[-1][len(URL_PARAM):]

    try:
        chrome_service = ChromeService(executable_path=os.path.join(os.getcwd(),"phantomjs.exe"))  # Replace with the path to chromedriver
        chrome_service.start()
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}

        chrome_instance = webdriver.Chrome(service=chrome_service, desired_capabilities=capabilities)
        chrome_instance.get(url)

        WebDriverWait(chrome_instance, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "comment-section-header-renderer"))
        )

        print("The video page is opened")

        def load_hidden_pages():
            load_btns = chrome_instance.find_elements_by_class_name("load-more-button")
            if len(load_btns) != 0:
                load_btns[0].click()
                time.sleep(1.5)
                load_hidden_pages()

        print("Loading hidden pages and comments")
        load_hidden_pages()

        def get_body():
            html = chrome_instance.execute_script(
                "if (document.getElementsByClassName('load-more-button').length === 0) { return document.body.innerHTML; }"
            )
            if html:
                return html
            else:
                time.sleep(10)
                return get_body()

        html = get_body()
        chrome_instance.quit()

        print("Contents are loaded")
        soup = BeautifulSoup(html, 'html.parser')
        res = []

        for elem in soup.select(".comment-thread-renderer"):
            root = elem.findChild()
            children = []

            for child_elem in elem.select(".comment-replies-renderer .comment-replies-renderer-pages .comment-renderer"):
                author = child_elem.select(".comment-renderer-header")[0].findChild()
                child = {
                    "comment": child_elem.select(".comment-renderer-text-content")[0].text,
                    "author": author.text,
                    "author_id": author.get("data-ytid"),
                    "like": check_like_score(child_elem.select(".comment-renderer-like-count.off")[0].text)
                }
                receiver = child_elem.select(".comment-renderer-text-content a")[0].text
                if receiver != "":
                    child["receiver"] = receiver
                children.append(child)

            author = root.select(".comment-author-text")[0]
            comment = {
                "root": root.select(".comment-renderer-text-content")[0].text,
                "author": author.text,
                "author_id": author.get("data-ytid"),
                "like": check_like_score(root.select(".comment-renderer-like-count.off")[0].text)
            }

            if children:
                comment["children"] = children

            res.append(comment)

        user = soup.select(".yt-user-info a")[0]
        return {
            "id": id,
            "channel": {
                "id": user["href"][len(URL_CHANNEL):],
                "name": user.text
            },
            "comments": res
        }

    except Exception as e:
        print(str(e))
        return None


def channel(id):
    if id.startswith(('http://', 'https://')):
        if not id.endswith("/about"):
            url = id + "/about"
        else:
            url = id
    else:
        url = "https://www.youtube.com/channel/" + id + "/about"

    try:
        chrome_service = ChromeService(executable_path=os.path.join(os.getcwd(),"phantomjs.exe"))  # Replace with the path to chromedriver
        chrome_service.start()
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}

        chrome_instance = webdriver.Chrome(service=chrome_service, desired_capabilities=capabilities)
        chrome_instance.get(url)

        html = chrome_instance.page_source
        chrome_instance.quit()

        soup = BeautifulSoup(html, 'html.parser')

        return {
            "id": id,
            "name": soup.select(".qualified-channel-title-text")[0].text,
            "description": soup.select(".about-description")[0].text.strip()
        }

    except Exception as e:
        print(str(e))
        return None


# Usage example:
# video_comments = comments("YOUR_YOUTUBE_VIDEO_URL")
# channel_info = channel("YOUR_YOUTUBE_CHANNEL_URL")
