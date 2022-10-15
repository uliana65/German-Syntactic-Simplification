import syntactic_rules as rules
from collections import defaultdict


class DocumentEval:
    """
    This class keeps and performs single document syntactic distribution statistics.
    It includes: POS, sentence length, clause number, NP length, apposition rate and length,
    relative/subordinated/coordinated/passive clauses rate and length
    """
    def __init__(self, doc, matcher):
        self.matcher = matcher
        self.document = doc    # spacy document
        self.sentNumber = 0
        for sent in doc.sents:
            if len(sent) > 1:
                self.sentNumber += 1
        self.tokenNumber = 0
        self.appNumber = 0
        self.npNumber = 0
        self.relNumber = 0
        self.clNumber = 0   # absolute
        self.coordNumber = 0
        self.subNumber = 0
        self.passNumber = 0

        self.sentLength = 0
        self.POSdistribution = defaultdict(float)
        pos = ["PROPN", "AUX", "DET", "ADJ", "NOUN", "PRON", "ADP", "CCONJ", "VERB", "NUM", "ADV", "SCONJ", "X", "PART", "SPACE", "INTJ", "PUNCT"]
        for p in pos:
            self.POSdistribution[p] = 0
        #self.DEPdistribution = defaultdict(float)
        self.npLength = 0
        self.APPrate = 0   # per sentence
        self.APPlength = 0

        self.clauseNumber = 0    # per sent
        self.relRate = 0
        self.relLength = 0
        self.coordRate = 0
        self.coordLength = 0
        self.subRate = 0
        self.subLength = 0
        self.passRate = 0
        self.passLength = 0

        for sent in doc.sents:
            if len(sent) > 1:
                self.tokenNumber += len(sent)
        self.sentLength = self.tokenNumber / self.sentNumber

    def distributions(self):
        np_ind = list()
        for sent in self.document.sents:
            # local stats
            for token in sent:
                self.POSdistribution[token.pos_] += 1
                #self.DEPdistribution[token.dep_] += 1
                if token.pos_ == "NOUN":
                    np_subtree = list([token.i for token in token.subtree])
                    np_ind.append(np_subtree)
                if token.pos_ == "AUX":
                    aux_children = [tok.pos_ for tok in token.children]
                    if "VERB" not in aux_children:
                        self.clNumber += 1
                if token.pos_ == "VERB":
                    self.clNumber += 1

            # appositions
            self.matcher.add("APP", rules.app_split_rule)
            matches = self.matcher(sent)
            for match in matches:
                self.appNumber += 1
                self.APPlength += len(list(sent[match[1]].subtree))
            self.matcher.remove("APP")

            # coordinated clauses
            self.matcher.add("COOR", rules.coordination_rule)
            matches = self.matcher(sent)
            for match in matches:
                self.coordNumber += 1
                coor_subtree = list(sent[match[1]].subtree)
                coor_deps = [token.dep_ for token in sent[match[1]].subtree]
                other_clauses = list()
                if "rc" in coor_deps:
                    ind = [i for i, x in enumerate(coor_deps) if x == "rc"]
                    for i in ind:
                        if coor_subtree[i] != sent[match[1]]:
                            other_clauses.extend(list(coor_subtree[i].subtree))
                if "cj" in coor_deps:
                    ind = [i for i, x in enumerate(coor_deps) if x == "cj"]
                    for i in ind:
                        if coor_subtree[i] != sent[match[1]]:
                            if coor_subtree[i].pos_ == "VERB" or coor_subtree[i].pos_ == "AUX":
                                other_clauses.extend(list(coor_subtree[i].subtree))
                if "cp" in coor_deps:
                    ind = [i for i, x in enumerate(coor_deps) if x == "cp"]
                    for i in ind:
                        if coor_subtree[i] != sent[match[1]]:
                            if coor_subtree[i].pos_ == "SCONJ":
                                other_clauses.extend(list(coor_subtree[i].subtree))
                coor_subtree = [token for token in coor_subtree if token not in other_clauses]
                self.coordLength += len(coor_subtree)
            self.matcher.remove("COOR")

            # subordinated clauses
            self.matcher.add("SUB", rules.subordinated_rule)
            matches = self.matcher(sent)
            for match in matches:
                self.subNumber += 1
                sub_subtree = list(sent[match[1]].subtree)
                sub_deps = [token.dep_ for token in sent[match[1]].subtree]
                other_clauses = list()
                if "rc" in sub_deps:
                    ind = [i for i, x in enumerate(sub_deps) if x == "rc"]
                    for i in ind:
                        if sub_subtree[i] != sent[match[1]]:
                            other_clauses.extend(list(sub_subtree[i].subtree))
                if "cj" in sub_deps:
                    ind = [i for i, x in enumerate(sub_deps) if x == "cj"]
                    for i in ind:
                        if sub_subtree[i] != sent[match[1]]:
                            if sub_subtree[i].pos_ == "VERB" or sub_subtree[i].pos_ == "AUX":
                                other_clauses.extend(list(sub_subtree[i].subtree))
                if "cp" in sub_deps:
                    ind = [i for i, x in enumerate(sub_deps) if x == "cp"]
                    for i in ind:
                        if sub_subtree[i] != sent[match[1]]:
                            if sub_subtree[i].pos_ == "SCONJ":
                                other_clauses.extend(list(sub_subtree[i].subtree))
                sub_subtree = [token for token in sub_subtree if token not in other_clauses]
                self.subLength += len(sub_subtree)
            self.matcher.remove("SUB")

            # relative clauses
            self.matcher.add("REL", rules.relative_rule)
            matches = self.matcher(sent)
            for match in matches:
                if "der" in [t.lemma_ for t in sent[match[1]].children]:
                    self.relNumber += 1
                    rel_subtree = list(sent[match[1]].subtree)
                    rel_deps = [token.dep_ for token in sent[match[1]].subtree]
                    other_clauses = list()
                    if "rc" in rel_deps:
                        ind = [i for i, x in enumerate(rel_deps) if x == "rc"]
                        for i in ind:
                            if rel_subtree[i] != sent[match[1]]:
                                other_clauses.extend(list(rel_subtree[i].subtree))
                    if "cp" in rel_deps:
                        ind = [i for i, x in enumerate(rel_deps) if x == "cp"]
                        for i in ind:
                            if rel_subtree[i] != sent[match[1]]:
                                if rel_subtree[i].pos_ == "SCONJ":
                                    other_clauses.extend(list(rel_subtree[i].subtree))
                    if "cj" in rel_deps:
                        ind = [i for i, x in enumerate(rel_deps) if x == "cj"]
                        for i in ind:
                            if rel_subtree[i] != sent[match[1]]:
                                if rel_subtree[i].pos_ == "VERB" or rel_subtree[i].pos_ == "AUX":
                                    other_clauses.extend(list(rel_subtree[i].subtree))
                    rel_subtree = [token for token in rel_subtree if token not in other_clauses]
                    self.relLength += len(rel_subtree)
            self.matcher.remove("REL")

            # passive clauses
            self.matcher.add("PASS", rules.passive_rule)
            matches = self.matcher(sent)
            for match in matches:
                self.passNumber += 1
                pass_subtree = list(sent[match[1]].subtree)
                pass_deps = [token.dep_ for token in sent[match[1]].subtree]
                other_clauses = list()
                if "rc" in pass_deps:
                    ind = [i for i, x in enumerate(pass_deps) if x == "rc"]
                    for i in ind:
                        if pass_subtree[i] != sent[match[1]]:
                            other_clauses.extend(list(pass_subtree[i].subtree))
                if "cp" in pass_deps:
                    ind = [i for i, x in enumerate(pass_deps) if x == "cp"]
                    for i in ind:
                        if pass_subtree[i] != sent[match[1]]:
                            if pass_subtree[i].pos_ == "SCONJ":
                                other_clauses.extend(list(pass_subtree[i].subtree))
                if "cj" in pass_deps:
                    ind = [i for i, x in enumerate(pass_deps) if x == "cj"]
                    for i in ind:
                        if pass_subtree[i] != sent[match[1]]:
                            if pass_subtree[i].pos_ == "VERB" or pass_subtree[i].pos_ == "AUX":
                                other_clauses.extend(list(pass_subtree[i].subtree))
                pass_subtree = [token for token in pass_subtree if token not in other_clauses]
                self.passLength += len(pass_subtree)
            self.matcher.remove("PASS")

        np_ind_true = [np for np in np_ind]
        for np in np_ind:
            for np1 in np_ind:
                if np != np1:
                    if np1[0] <= np[0] and np[-1] <= np1[-1]:
                        try:
                            np_ind_true.remove(np)
                        except ValueError:
                            continue
                    elif np[0] <= np1[0] and np1[-1] <= np[-1]:
                        try:
                            np_ind_true.remove(np1)
                        except ValueError:
                            continue

        self.npNumber += len(np_ind_true)
        self.npLength += sum(sum(np_ind_true, []))

        if self.npNumber:
            self.npLength = round(self.npLength / self.npNumber, 4)
        else:
            self.npLength = round(self.npLength / 1, 4)
        if self.tokenNumber:
            self.POSdistribution = {pos: round(n / self.tokenNumber, 4) for pos, n in self.POSdistribution.items()}
            #self.DEPdistribution = {dep: round(n / self.tokenNumber, 4) for dep, n in self.DEPdistribution.items()}
        else:
            self.POSdistribution = {pos: round(n / 1, 4) for pos, n in self.POSdistribution.items()}
            #self.DEPdistribution = {dep: round(n / 1, 4) for dep, n in self.DEPdistribution.items()}
        if self.sentNumber:
            self.APPrate = round(self.appNumber / self.sentNumber, 4)
        else:
            self.APPrate = round(self.appNumber / 1, 4)
        if self.appNumber:
            self.APPlength = round(self.APPlength / self.appNumber, 4)
        else:
            self.APPlength = round(self.APPlength / 1, 4)

        if self.clNumber:
            self.coordRate = round(self.coordNumber / self.clNumber, 4)
            self.subRate = round(self.subNumber / self.clNumber, 4)
            self.relRate = round(self.relNumber / self.clNumber, 4)
            self.passRate = round(self.passNumber / self.clNumber, 4)
        else:
            self.coordRate = round(self.coordNumber / 1, 4)
            self.subRate = round(self.subNumber / 1, 4)
            self.relRate = round(self.relNumber / 1, 4)
            self.passRate = round(self.passNumber / 1, 4)
        if self.sentNumber:
            self.clauseNumber = round(self.clNumber / self.sentNumber, 4)
        else:
            self.clauseNumber = round(self.clNumber / 1, 4)
        if self.coordNumber:
            self.coordLength = round(self.coordLength / self.coordNumber, 4)
        else:
            self.coordLength = round(self.coordLength / 1, 4)
        if self.subNumber:
            self.subLength = round(self.subLength / self.subNumber, 4)
        else:
            self.subLength = round(self.subLength / 1, 4)
        if self.relNumber:
            self.relLength = round(self.relLength / self.relNumber, 4)
        else:
            self.relLength = round(self.relLength / 1, 4)
        if self.passNumber:
            self.passLength = round(self.passLength / self.passNumber, 4)
        else:
            self.passLength = round(self.passLength / 1, 4)


class CorpusEval:
    """
    This class keeps and counts syntactic distribution statistics for the whole corpus
    It includes: POS, sentence length, clause number, NP length, apposition rate and length,
    relative/subordinated/coordinated/passive clauses rate and length
    """
    def __init__(self, documentCollection: list):
        self.corpus = documentCollection
        self.docNumber = len(documentCollection)

        self.sentLength = round(sum([doc.sentLength for doc in self.corpus])/self.docNumber, 4)
        self.POSdistribution = defaultdict(float)
        #self.DEPdistribution = defaultdict(float)
        self.npLength = round(sum([doc.npLength for doc in self.corpus])/self.docNumber, 4)
        self.appRate = round(sum([doc.APPrate for doc in self.corpus])/self.docNumber, 4)
        self.appLength = round(sum([doc.APPlength for doc in self.corpus])/self.docNumber, 4)

        self.clauseNumber = round(sum([doc.clauseNumber for doc in self.corpus])/self.docNumber, 4)
        self.relRate = round(sum([doc.relRate for doc in self.corpus])/self.docNumber, 4)
        self.relLength = round(sum([doc.relLength for doc in self.corpus])/self.docNumber, 4)
        self.coordRate = round(sum([doc.coordRate for doc in self.corpus])/self.docNumber, 4)
        self.coordLength = round(sum([doc.coordLength for doc in self.corpus])/self.docNumber, 4)
        self.subRate = round(sum([doc.subRate for doc in self.corpus])/self.docNumber, 4)
        self.subLength = round(sum([doc.subLength for doc in self.corpus])/self.docNumber, 4)
        self.passRate = round(sum([doc.passRate for doc in self.corpus])/self.docNumber, 4)
        self.passLength = round(sum([doc.passLength for doc in self.corpus])/self.docNumber, 4)

        for document in self.corpus:
            for pos in document.POSdistribution:
                self.POSdistribution[pos] += document.POSdistribution[pos]
            #for dep in document.DEPdistribution:
                #self.DEPdistribution[dep] += document.DEPdistribution[dep]
        self.POSdistribution = {pos: round(n / self.docNumber, 4) for pos, n in self.POSdistribution.items()}
        #self.DEPdistribution = {dep: round(n / self.docNumber, 4) for dep, n in self.DEPdistribution.items()}
