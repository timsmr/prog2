import db
from scraputils import get_news


def data_saver(url, n=1):
    data = get_news(url, n)
    s = db.session()
    for i in data:
        news = db.News(
            title=i["title"],
            author=i["author"],
            url=i["url"],
            comments=i["comments"],
            points=i["points"],
        )
        s.add(news)
        s.commit()


if __name__ == "__main__":
    url = "https://news.ycombinator.com/newest"
    n = 34
    data_saver(url, n)
