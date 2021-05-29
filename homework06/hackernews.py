import pathlib
import pickle
import typing as tp

from bottle import redirect, request, route, run, template

import stemmer
from bayes import NaiveBayesClassifier
from db import News, session
from scraputils import get_news


@route("/news")
def news_list():
    s = session()
    rows = s.query(News).filter(News.label == None).all()
    return template("news_template", rows=rows)


@route("/add_label/")
def add_label():
    params = request.query
    s = session()
    entry = s.query(News).filter(News.id == params["id"]).first()
    entry.label = params["label"]
    s.commit()
    redirect("/news")


@route("/update")
def update_news():
    data = get_news("https://news.ycombinator.com/newest")
    s = session()
    marker = s.query(News).first()
    batch_size = 30
    for i, e in enumerate(data):
        if e["title"] == marker.title and e["author"] == marker.author:
            batch_size = i
    data = data[:batch_size]
    for i in data:
        new = News(
            title=i["title"],
            author=i["author"],
            url=i["url"],
            comments=i["comments"],
            points=i["points"],
        )
        s.add(new)
        s.commit()
    redirect("/news")


@route("/classify")
def classify_news():
    s = session()
    unclassified: tp.List[tp.Tuple[int, str]] = [
        (i.id, stemmer.clear(i.title)) for i in s.query(News).filter(News.label == None).all()
    ]
    X: tp.List[str] = [i[1] for i in unclassified]
    if not pathlib.Path("model/model.pickle").is_file():
        raise ValueError(
            "Классификатор не натренирован! Пожалуйста, разметь новости, чтобы нормально можно было натренировать модель."
        )
    with open("model/model.pickle", "rb") as model_file:
        model = pickle.load(model_file)
    labels = model.predict(X)
    for i, e in enumerate(unclassified):
        extract = s.query(News).filter(News.id == e[0]).first()
        extract.label = labels[i]
        s.commit()
    rows = s.query(News).filter(News.label != None).order_by(News.label).all()
    return template("classified_template", rows=rows)


if __name__ == "__main__":
    run(host="localhost", port=8080)
