"""
This module provides the Flesch score for a German text.
"""


def flesch_formula(syllables_per_hundred_words, words_per_sentence):
    reading_ease_score = 180 - 58.5 * syllables_per_hundred_words - words_per_sentence
    return round(reading_ease_score, 5)


def syllable_count(word):
    """
    Counts syllables by assuming that a syllable is a vowel
    or an uninterrupted succession of vowels inside one word
    :param word: string corresponding to a word
    :return: int corresponding to a syllable number
    """
    vowels = ["a", "e", "i", "o", "u", "y"]
    syl_ind_prev = 0
    syl_number = 0
    for letter in range(len(word)):
        if word[letter] in vowels:
            if letter-1 == syl_ind_prev:
                continue
            else:
                syl_number += 1
                syl_ind_prev = letter
    return syl_number


class Counter:
    def __init__(self):
        """
        Keeps stats for the score calculation and the score itself
        """
        self.syllables = 0

        self.sentences = 0
        self.words = 0
        self.easiness_score = 0

    def count_doc(self, doc):
        """
        Counts words, sentences and syllables for a document
        :param doc: spaCy text object
        """
        for sent in doc.sents:
            if len(sent) > 1:
                self.sentences += 1
                self.words += len(sent)
                for word in sent:
                    if word and word.pos_ != "PUNCT":
                        self.syllables += syllable_count(word.text)

    def flesch_stats(self):
        """
        Calculates final Flesch score for the whole corpus
        """
        words_per_sent = self.words / self.sentences
        syllables_per_word = self.syllables / self.words
        self.easiness_score = flesch_formula(syllables_per_word, words_per_sent)
