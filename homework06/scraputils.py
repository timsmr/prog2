import requests
from bs4 import BeautifulSoup


def extract_news(parser):
    """ Extract news from a given web page """
    news_list = []

    # find all trs in the body

    tr = parser.body.findAll("table", {"class": "itemlist"})[0].findAll("tr")

    i = 0

    # dictionaty which we append to the news_list
    d = {"author": None, "comments": None, "points": None, "title": None, "url": None}

    while i < 90:
        # id of the news
        n = "item?id=" + tr[i].get("id")
        d["title"] = tr[i].findAll("a", {"class": "storylink"})[0].text
        d["url"] = tr[i].findAll("a", {"class": "storylink"})[0].get("href")
        i += 1
        d["author"] = tr[i].findAll("a", {"class": "hnuser"})[0].text
        d["points"] = int(tr[i].findAll("span", {"class": "score"})[0].text.split()[0])
        com = tr[i].findAll("a", {"href": n})[0].text
        if com == "discuss":
            d["comments"] = 0
        else:
            d["comments"] = int(com.split()[0])
        i += 2
        news_list.append(d.copy())
    return news_list


def extract_next_page(parser):
    """ Extract next page URL """
    return parser.findAll("a", {"class": "morelink"})[0].get("href")


def get_news(url, n_pages=1):
    """ Collect news from a given web page """
    news = []
    while n_pages:
        print("Collecting data from page: {}".format(url))
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = extract_news(soup)
        next_page = extract_next_page(soup)
        url = "https://news.ycombinator.com/" + next_page
        news.extend(news_list)
        n_pages -= 1
    return news
