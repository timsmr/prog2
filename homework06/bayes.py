import itertools
import math
import operator
import pathlib
import pickle
import typing as tp
from collections import Counter, defaultdict
from copy import deepcopy

import stemmer
from db import News, session


class NaiveBayesClassifier:
    def __init__(self, alpha):
        if not (0.0 < alpha <= 1.0):
            raise ValueError("Альфа должна быть человеческой, а не корявой")
        self.class_probs = []  # Вероятности классов
        self.alpha = alpha  # Сглаживающий параметр
        self.doc_count = 0  # Размер датасета
        self.unique_words = []
        self.words_per_class = []  # Сколько раз слова встречаются в классах. Словарь словарей
        self.class_lengths = []  # Количество слов в классе
        self.word_probs = []  # Вероятность встретить слово в классе

    def fit(self, X, y):
        """ Fit Naive Bayes classifier according to X, y. """
        if not X or not y:
            raise ValueError(
                "Отвратительный датасет! Либо пустой, либо лень разметить что ли было?"
            )
        self.doc_count = len(
            X
        )  # X - список строк, где каждая строка - новость. А Y - список строк, где каждая строка - метка класса.
        self.class_probs = Counter(y)  # Сколько раз определённая метка встречается в датасете
        for e in self.class_probs:
            self.class_probs[e] /= len(y)
        self.unique_words = [i.split(" ") for i in X]  # Список списков слов
        self.unique_words = list(
            itertools.chain.from_iterable(self.unique_words)
        )  # Длинный список слов с повторами
        self.unique_words = sorted(list(set(self.unique_words)))  # Список уникальных слов
        self.words_per_class = defaultdict(str)  # Создаём словарь без исключений
        self.class_lengths = defaultdict(int)  # Тут мы храним числа
        for i, string in enumerate(X):
            words = string.split(" ")  # Делим новость на слова
            c = y[i]  # Це отметка для цей новини
            self.class_lengths[c] += len(words)  # Записываем количество слов в классе
            for word in words:
                if not word in self.words_per_class.keys():
                    self.words_per_class[word] = {
                        key: value for (key, value) in zip(list(set(y)), [0 for _ in list(set(y))])
                    }  # "денис": {'good': 0, 'maybe': 0, 'never':0}
                self.words_per_class[word][
                    c
                ] += 1  # Добавляем единицу к words_per_class[слово][отметка]
        self.word_probs = deepcopy(self.words_per_class)
        for word, value in self.word_probs.items():
            for c, _ in value.items():
                self.word_probs[word][c] = (self.word_probs[word][c] + self.alpha) / (
                    self.class_lengths[c] + self.alpha * len(self.unique_words)
                )  # Формула вероятности слова
        return

    def predict(self, X):
        """ Perform classification on an array of test vectors X. """
        if (
            not self.class_probs
            or not self.doc_count
            or not self.unique_words
            or not self.words_per_class
            or not self.class_lengths
            or not self.word_probs
        ):
            raise ValueError("Модель не натренирована. Иди тренируй")
        labels = []
        for document in X:
            words = document.split(" ")  # Делим новости на слова
            probabilities = defaultdict(int)  # Вероятности для данной новости
            for c in self.class_lengths.keys():
                word_probs_sum = []  # Список натуральных логарифмов вероятности слов
                for word in words:  # Идём по словам в новости
                    if word in self.unique_words:  # Если слово встречалось раньше
                        word_probs_sum.append(
                            math.log(self.word_probs[word][c])
                        )  # К word_probs_sum добавляем логарифм вероятности встретить слово в классе
                word_probs_sum = sum(word_probs_sum)
                probabilities[c] = (
                    math.log(self.class_probs[c]) + word_probs_sum
                )  # К логарифму вероятности встретить данный класс в датасете добавляем сумму логарифмов вероятностей встретить слова в классе
            predicted_label = max(probabilities.items(), key=operator.itemgetter(1))[
                0
            ]  # https://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
            labels.append(predicted_label)
        return labels

    def score(self, X_test, y_test):
        """ Returns the mean accuracy on the given test data and labels. """
        predicted = self.predict(X_test)
        class_accuracies = defaultdict(float)
        for c in list(set(y_test)):
            if y_test.count(c):
                true_positives = sum(
                    [1 for i, e in enumerate(predicted) if e == c and y_test[i] == c]
                )
                false_negatives = sum(
                    [1 for i, e in enumerate(predicted) if e != c and y_test[i] == c]
                )
                class_accuracies[c] = true_positives / (true_positives + false_negatives)
        score = sum([i for i in class_accuracies.values()]) / len(list(set(y_test)))
        return score


if __name__ == "__main__":
    if not pathlib.Path("model/model.pickle").is_file():
        print("Модели нету. Создаю...")
        model = NaiveBayesClassifier(alpha=0.1)
        print("Достаю твои новости из датабазы")
        s = session()
        classified = [(i.title, i.label) for i in s.query(News).filter(News.label != None).all()]
        X_train, y_train = [], []
        for label, extract in classified:
            X_train.append(label)
            y_train.append(extract)
        X_train = [stemmer.clear(x).lower() for x in X_train]
        print(f"Достано {len(X_train)} промаркированных новостей")
        print("Тренируюсь...")
        model.fit(X_train, y_train)
        print("Модель натренирована. Сохраняю...")
        with open("model/model.pickle", "wb") as model_file:
            pickle.dump(model, model_file)
        print("Сохранил!")
    else:
        print(f"Модель уже существует")
