import spacy
from spacy.matcher import Matcher
import distributions as dist
import matplotlib.pyplot as plt
import numpy as np
import flesch
import sys
import jsonlines


if __name__ == "__main__":
    """
    This module outputs Flesch scores and syntactic distribution plots for the original, transformed and target corpora.
    Input: original file with texts and their targets (.txt or .jsonl) and a file with transformed texts
    """
    # initiate distributions
    newDocumentsStats = list()
    oldDocumentsStats = list()
    targetDocumentsStats = list()

    # initiate flesch scores
    new_easiness_score = flesch.Counter()
    old_easiness_score = flesch.Counter()
    target_easiness_score = flesch.Counter()

    original_path = sys.argv[1]
    transformed_path = sys.argv[2]
    nlp = spacy.load("de_core_news_lg")
    matcher = Matcher(nlp.vocab)
    ind = original_path.index(".")

    # get original and target stats
    if "txt" in original_path[-3:]:
        with open(original_path, "r", encoding="utf-8") as f:
            line_number = 0
            line = f.readline().strip()
            id = 0
            while line:
                line_number += 1
                try:
                    if "###ID###" in line:
                        line = f.readline().strip()
                        line = line.replace("#", "", 6)
                        id = int(line)
                        line_number += 1
                        line = f.readline().strip()
                    elif "###ORIG###" in line:
                        doc = ''
                        while line:
                            line = f.readline().strip()
                            if line and "###TARG###" not in line and "###ID###" not in line:
                                line_number += 1
                                doc += line
                            else:
                                break
                        oldDoc = nlp(doc)
                        old_easiness_score.count_doc(oldDoc)
                        oldDocStats = dist.DocumentEval(oldDoc, matcher)
                        oldDocStats.distributions()
                        oldDocumentsStats.append(oldDocStats)

                    elif "###TARG###" in line:
                        target_text = ''
                        while line:
                            line = f.readline().strip()
                            if line and "###ID###" not in line:
                                line_number += 1
                                target_text += line
                            else:
                                break
                        targetDoc = nlp(target_text)
                        target_easiness_score.count_doc(targetDoc)
                        targetDocStats = dist.DocumentEval(targetDoc, matcher)
                        targetDocStats.distributions()
                        targetDocumentsStats.append(targetDocStats)

                except KeyError:
                    print(f"Invalid data file structure or formatting in line {line_number}. \nSee README to comply with data file requirements.")

    elif "jsonl" in original_path[-5:]:
        with jsonlines.open(original_path) as orig:
            for doc in orig:
                oldDoc = nlp(" ".join(doc['wiki_sentences']))
                old_easiness_score.count_doc(oldDoc)
                oldDocStats = dist.DocumentEval(oldDoc, matcher)
                oldDocStats.distributions()
                oldDocumentsStats.append(oldDocStats)

                targetDoc = nlp(" ".join(doc['klexikon_sentences']))
                target_easiness_score.count_doc(targetDoc)
                targetDocStats = dist.DocumentEval(targetDoc, matcher)
                targetDocStats.distributions()
                targetDocumentsStats.append(targetDocStats)

    # get transformed stats
    with open(transformed_path, "r", encoding="utf-8") as f:
        line = f.readline().strip()
        id = 0
        while line:
            if "###ID###" in line:
                line = f.readline().strip()
                line = line.replace("#", "", 6)
                id = int(line)
                line = f.readline().strip()
            elif "###SIMP###" in line or "###SUMM###" in line:
                doc = ''
                while line:
                    line = f.readline().strip()
                    if line and "###ID###" not in line:
                        doc += line
                    else:
                        break
                newDoc = nlp(doc)
                new_easiness_score.count_doc(newDoc)
                newDocStats = dist.DocumentEval(newDoc, matcher)
                newDocStats.distributions()
                newDocumentsStats.append(newDocStats)

    # get overall corpus stats
    oldCorpusStats = dist.CorpusEval(oldDocumentsStats)
    newCorpusStats = dist.CorpusEval(newDocumentsStats)
    targetCorpusStats = dist.CorpusEval(targetDocumentsStats)

    # get flesch scores
    target_easiness_score.flesch_stats()
    new_easiness_score.flesch_stats()
    old_easiness_score.flesch_stats()

    print(f'Flesch Easiness Scores:')
    print(f"    TARGET TEXTS: {target_easiness_score.easiness_score}")
    print(f"    TRANSFORMED TEXTS: {new_easiness_score.easiness_score}")
    print(f"    ORIGINAL TEXTS: {old_easiness_score.easiness_score}")

    # plot syntactic distributions
    # POS
    barWidth = 0.25
    fig4 = plt.subplots(figsize=(20, 13))
    orderedTarget = {k: v for k, v in sorted(targetCorpusStats.POSdistribution.items())}
    orderedOld = {k: v for k, v in sorted(oldCorpusStats.POSdistribution.items())}
    orderedNew = {k: v for k, v in sorted(newCorpusStats.POSdistribution.items())}

    target = [pos for pos in orderedTarget.values()]
    old = [pos for pos in orderedOld.values()]
    new = [pos for pos in orderedNew.values()]

    br1_4 = np.arange(len(target))
    br2_4 = [x + barWidth for x in br1_4]
    br3_4 = [x + barWidth for x in br2_4]
    plt.bar(br1_4, target, color="forestgreen", width=barWidth, label="Target Corpus")
    plt.bar(br2_4, new, color="deepskyblue", width=barWidth, label="Transformed Corpus")
    plt.bar(br3_4, old, color="red", width=barWidth, label="Original Corpus")
    plt.xlabel("Part of Speech")
    plt.ylabel("Average Proportion")
    plt.xticks([r + barWidth for r in range(len(target))], [pos for pos in orderedTarget.keys()])
    plt.legend()

    plt.show()

    # sentence/np length, clause number
    barWidth = 0.25
    fig7 = plt.subplots(figsize=(6, 10))
    target = [targetCorpusStats.sentLength, targetCorpusStats.clauseNumber]
    old = [oldCorpusStats.sentLength, oldCorpusStats.clauseNumber]
    new = [newCorpusStats.sentLength, newCorpusStats.clauseNumber]

    br1_7 = np.arange(len(target))
    br2_7 = [x + barWidth for x in br1_7]
    br4_7 = [x + barWidth for x in br2_7]
    plt.bar(br1_7, target, color="forestgreen", width=barWidth, label="Target Corpus")
    plt.bar(br2_7, new, color="deepskyblue", width=barWidth, label="Transformed Corpus")
    plt.bar(br4_7, old, color="red", width=barWidth, label="Original Corpus")
    plt.xlabel("Metric")
    plt.ylabel("Average Number/Length")
    plt.xticks([r + barWidth for r in range(len(target))], ["Sentence Length", "Clause Number"])
    plt.legend()

    plt.show()

    # rates for clauses
    barWidth = 0.25
    fig1 = plt.subplots(figsize=(8, 10))
    target = [targetCorpusStats.appRate, targetCorpusStats.relRate, targetCorpusStats.subRate, targetCorpusStats.coordRate, targetCorpusStats.passRate]
    old = [oldCorpusStats.appRate, oldCorpusStats.relRate, oldCorpusStats.subRate, oldCorpusStats.coordRate, oldCorpusStats.passRate]
    new = [newCorpusStats.appRate, newCorpusStats.relRate, newCorpusStats.subRate, newCorpusStats.coordRate, newCorpusStats.passRate]
    br1_1 = np.arange(len(target))
    br2_1 = [x + barWidth for x in br1_1]
    br4_1 = [x + barWidth for x in br2_1]
    plt.bar(br1_1, target, color="forestgreen", width=barWidth, label="Target Corpus")
    plt.bar(br2_1, new, color="deepskyblue", width=barWidth, label="Transformed Corpus")
    plt.bar(br4_1, old, color="red", width=barWidth, label="Original Corpus")
    plt.xlabel("Metric")
    plt.ylabel("Average Proportion")
    plt.xticks([r + barWidth for r in range(len(target))], ["Appositon", "Relative Cl", "Subordinated Cl", "Coordinated Cl", "Passive Cl"])
    plt.legend()

    plt.show()

    # clause length
    barWidth = 0.25
    fig3 = plt.subplots(figsize=(8, 10))
    target = [targetCorpusStats.appLength, targetCorpusStats.relLength, targetCorpusStats.subLength, targetCorpusStats.coordLength, targetCorpusStats.passLength]
    old = [oldCorpusStats.appLength, oldCorpusStats.relLength, oldCorpusStats.subLength, oldCorpusStats.coordLength, oldCorpusStats.passLength]
    new = [newCorpusStats.appLength, newCorpusStats.relLength, newCorpusStats.subLength, newCorpusStats.coordLength, newCorpusStats.passLength]
    br1_3 = np.arange(len(target))
    br2_3 = [x + barWidth for x in br1_3]
    br4_3 = [x + barWidth for x in br2_3]
    plt.bar(br1_3, target, color="forestgreen", width=barWidth, label="Target Corpus")
    plt.bar(br2_3, new, color="deepskyblue", width=barWidth, label="Transformed Corpus")
    plt.bar(br4_3, old, color="red", width=barWidth, label="Original Corpus")
    plt.xlabel("Metric")
    plt.ylabel("Average Length")
    plt.xticks([r + barWidth for r in range(len(target))], ["Appositon", "Relative Cl", "Subordinated Cl", "Coordinated Cl", "Passive Cl"])
    plt.legend()

    plt.show()
