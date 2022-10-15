import spacy
from spacy.matcher import Matcher
import syntactic_rules as rules
import jsonlines
import re
import json
from collections import defaultdict
import sys


def normalize_punct(text):
    text = re.sub(" \.", ".", text)
    result = re.search(rules.punt_regex, text)
    if result:
        new_text = text[:result.start()] + text[result.end()-1:]
        final_text = normalize_punct(new_text)
        return final_text
    else:
        return text


class Simplifier:
    """
    This class keeps a transformed sentence and the sentences detached from it.
    """
    def __init__(self, sentence):
        """
        :param sentence: spaCy object (parsed sentence)
        """
        self.transformed_sentence = sentence
        self.detached_sentences = list()
        self.rules = list()

    def correct_to_case(self, token_old, token_new: str, oneWord: bool):
        features = list(token_old.morph)

        if not features or ("Case=Nom" in features and "Number=Sing" in features) or ("Case=Acc" in features and "Number=Sing" in features):
            return token_new
        else:
            if "Number=Plur" in features:
                    if "Gender=Fem" in features:
                        if oneWord:
                            if token_new[-1] == "e":
                                return token_new + "n"
                            else:
                                return token_new + "en"
                        else:
                            if "Case=Nom" in features:
                                return token_new
                            else:
                                tok1, tok2 = token_new.split(" ")
                                tok1 += "n"
                                return tok1 + " " + tok2
                    elif "Gender=Neut" in features:
                        if "Case=Nom" in features or "Case=Gen" in features:
                            special_cases = ["hnt", "ahr", "ert", "end"]
                            if token_new[-3:] in special_cases:
                                return token_new + "e"
                            else:
                                return token_new
                        elif "Case=Acc" in features:
                            return token_new
                        elif "Case=Dat" in features:
                            special_cases = ["mm", "tt", "ar", "tz", "rd", "ty", "ck"]
                            if token_new[-2:] in special_cases:
                                return token_new
                            else:
                                vowels = ["a", "e", "i", "o", "u", "y"]
                                if token_new[-2] in vowels:
                                    return token_new + "n"
                                else:
                                    return token_new + "en"
                    elif "Gender=Masc" in features:
                        if "Case=Nom" in features or "Case=Gen" in features:
                            special_cases = ["tt", "kt", "at", "ag"]
                            if token_new[-2:] in special_cases:
                                return token_new + "e"
                            else:
                                return token_new
                        elif "Case=Acc" in features:
                            return token_new
                        elif "Case=Dat" in features:
                            special_cases = ["ad", "ro", "ar", "uß"]
                            if token_new[-2:] in special_cases:
                                return token_new
                            else:
                                vowels = ["a", "e", "i", "o", "u", "y"]
                                if token_new[-2] in vowels:
                                    return token_new + "n"
                                else:
                                    return token_new + "en"

            elif "Number=Sing" in features:
                    if "Gender=Fem" in features:
                        if oneWord:
                            return token_new
                        else:
                            tok1, tok2 = token_new.split(" ")
                            tok1 += "n"
                            return tok1 + " " + tok2
                    elif "Gender=Neut" in features:
                        if "Case=Dat" in features:
                            return token_new
                        elif "Case=Gen" in features:
                            special_cases = ["nt", "tz", "hr"]
                            if token_new == "Hertz":
                                return token_new
                            elif token_new[-2:] in special_cases:
                                return token_new + "es"
                            else:
                                return token_new + 's'
                    elif "Gender=Masc" in features:
                        if "Case=Dat" in features:
                            return token_new
                        elif "Case=Gen" in features:
                            vowels = ["a", "e", "i", "o", "u", "y"]
                            if token_new[-1] == "ß" or token_new[-2:] == "ag":
                                return token_new + "es"
                            if token_new[-2] in vowels:
                                return token_new + "s"
                            else:
                                return token_new + "es"


        return token_new

    def correct_to_nominative(self, token_app, token_head, app_phrase:list, sbp=False):
        #TODO: don't change comparative/superlative to lemma
        features = list(token_app.morph)
        if token_app.pos_ != "NOUN" or token_app.pos_ != "PNOUN":
            features = list(token_head.morph)

        if "Case=Nom" in features:
            return [token.text for token in app_phrase]
        else:
            app_pp = list()
            app_tail = list()
            if not sbp:
                app_phrase_correct = [token if token.i <= token_app.i else app_tail.append(token.text) for token in app_phrase]
                app_phrase_correct = [token for token in app_phrase_correct if token]
            else:
                app_phrase_correct = app_phrase
            #print(f"FIRST: {app_phrase_correct}")

            for token in app_phrase_correct:
                if token.pos_ == "ADP":
                    app_pp.extend(token.subtree)
                elif token.lemma_ == "der" and (self.transformed_sentence[token.i-1].lemma_ == "ein" or self.transformed_sentence[token.i-1].lemma_ == "einer"):
                    app_pp.extend(token.head.subtree)

            superlatives = []
            for token in app_phrase_correct:
                try:
                    if "ste" in token.text[-4:-1] or "ßte" in token.text[-4:-1]:
                        superlatives.append(token.text)
                except IndexError:
                    continue

            if "Number=Sing" in features:
                if "Gender=Fem" in features:
                    app_phrase_correct = [app_phrase_correct[ind].lemma_ + "e" if ind < len(app_phrase_correct)-1 and app_phrase_correct[ind] not in app_pp and app_phrase_correct[ind].text not in superlatives else app_phrase_correct[ind].text for ind in range(len(app_phrase_correct))]
                    #print(f"SECONDFE: {app_phrase_correct}")
                    if "dere" in app_phrase_correct:
                        app_phrase_correct[app_phrase_correct.index("dere")] = "die"
                    app_phrase_correct = [token[:-1] if token[-1] != "e" and token in superlatives else token for token in app_phrase_correct]
                    #print(f"THIRDFE: {app_phrase_correct}")
                elif "Gender=Neut" in features:
                    detPronInd = False
                    #print(f"SECONDN: {app_phrase_correct}")
                    for ind in range(len(app_phrase_correct)):
                        if app_phrase_correct[ind].pos_ == "DET":
                            if app_phrase_correct[ind].lemma_ == "der":
                                app_phrase_correct[ind] = "das"
                            elif app_phrase_correct[ind].lemma_ == "dieser":
                                app_phrase_correct[ind] = "dieses"
                            else:
                                app_phrase_correct[ind] = app_phrase_correct[ind].lemma_
                                detPronInd = True
                            #print(f"THIRDN: {app_phrase_correct}")
                        elif app_phrase_correct[ind].pos_ == "ADJ":
                            if detPronInd:
                                if app_phrase_correct[ind].text not in superlatives:
                                    app_phrase_correct[ind] = app_phrase_correct[ind].lemma_ + "es"
                                else:
                                    if app_phrase_correct[ind].text[-1] != "e":
                                        app_phrase_correct[ind] = app_phrase_correct[ind].text[:-1]
                            else:
                                if app_phrase_correct[ind].text not in superlatives:
                                    app_phrase_correct[ind] = app_phrase_correct[ind].lemma_ + "e"
                                else:
                                    if app_phrase_correct[ind].text[-1] != "e":
                                        app_phrase_correct[ind] = app_phrase_correct[ind].text[:-1]
                            #print(f"FOURTHN: {app_phrase_correct}")
                        else:
                            if app_phrase_correct[ind] not in app_pp:
                                app_phrase_correct[ind] = app_phrase_correct[ind].lemma_
                            else:
                                app_phrase_correct[ind] = app_phrase_correct[ind].text
                            #print(f"FIFTHN: {app_phrase_correct}")
                elif "Gender=Masc" in features:
                    detPronInd = False
                    #print(f"SECOND: {app_phrase_correct}")
                    for ind in range(len(app_phrase_correct)):
                        if app_phrase_correct[ind].pos_ == "DET":
                            if app_phrase_correct[ind].lemma_ == "der" or app_phrase_correct[ind].lemma_ == "dieser":
                                app_phrase_correct[ind] = app_phrase_correct[ind].lemma_
                            else:
                                app_phrase_correct[ind] = app_phrase_correct[ind].lemma_
                                detPronInd = True
                            #print(f"THIRD: {app_phrase_correct}")
                        elif app_phrase_correct[ind].pos_ == "ADJ":
                            if detPronInd:
                                if app_phrase_correct[ind].text not in superlatives:
                                    app_phrase_correct[ind] = app_phrase_correct[ind].lemma_ + "er"
                                else:
                                    if app_phrase_correct[ind].text[-1] != "e":
                                        app_phrase_correct[ind] = app_phrase_correct[ind].text[:-1]
                                #print(f"FOURTH: {app_phrase_correct}")
                            else:
                                if app_phrase_correct[ind].text not in superlatives:
                                    app_phrase_correct[ind] = app_phrase_correct[ind].lemma_ + "e"
                                else:
                                    if app_phrase_correct[ind].text[-1] != "e":
                                        app_phrase_correct[ind] = app_phrase_correct[ind].text[:-1]
                                #print(f"FIFTH: {app_phrase_correct}")
                        else:
                            if app_phrase_correct[ind] not in app_pp:
                                app_phrase_correct[ind] = app_phrase_correct[ind].lemma_
                            else:
                                app_phrase_correct[ind] = app_phrase_correct[ind].text
                            #print(f"SIXTH: {app_phrase_correct}")

            else:
                det = False
                for ind in range(len(app_phrase_correct)):
                    if app_phrase_correct[ind].pos_ == "DET":
                        det = True
                        if app_phrase_correct[ind].lemma_ == "der":
                            app_phrase_correct[ind] = "die"
                        elif app_phrase_correct[ind].lemma_ == "dieser":
                            app_phrase_correct[ind] = "diese"
                        else:
                            app_phrase_correct[ind] = app_phrase_correct[ind].lemma_ + "e"
                    elif app_phrase_correct[ind].pos_ == "ADJ":
                        if det:
                            if app_phrase_correct[ind].text not in superlatives:
                                app_phrase_correct[ind] = app_phrase_correct[ind].lemma_ + "en"
                            else:
                                if app_phrase_correct[ind].text[-1] != "e":
                                    app_phrase_correct[ind] = app_phrase_correct[ind].text[:-1]
                        else:
                            if app_phrase_correct[ind].text not in superlatives:
                                app_phrase_correct[ind] = app_phrase_correct[ind].lemma_ + "e"
                            else:
                                if app_phrase_correct[ind].text[-1] != "e":
                                    app_phrase_correct[ind] = app_phrase_correct[ind].text[:-1]
                    elif app_phrase_correct[ind].text == token_app.text and token_app.pos_ == "NOUN":
                        if "Case=Dat" in features:
                            vowels = ["a", "e", "i", "o", "u", "y"]
                            if app_phrase_correct[ind].text != app_phrase_correct[ind].lemma_:
                                if app_phrase_correct[ind].text[-1] == "n" and app_phrase_correct[ind].text[-2] not in vowels:
                                    app_phrase_correct[ind] = app_phrase_correct[ind].text[:-1]
                                else:
                                    app_phrase_correct[ind] = app_phrase_correct[ind].text
                            else:
                                app_phrase_correct[ind] = app_phrase_correct[ind].text
                        else:
                            app_phrase_correct[ind] = app_phrase_correct[ind].text
                    else:
                        if app_phrase_correct[ind] not in app_pp:
                            app_phrase_correct[ind] = app_phrase_correct[ind].lemma_
                        else:
                            app_phrase_correct[ind] = app_phrase_correct[ind].text

            app_phrase_correct.extend(app_tail)

            for ind in range(len(app_phrase_correct)):
                try:
                    app_phrase_correct[ind] = app_phrase_correct[ind].text
                except:
                    continue

            return app_phrase_correct

    def correct_to_accusative(self, token):
        features = list(token.morph)
        if "Gender=Masc" in features:
            object = []
            for t in token.subtree:
                if t.pos_ == "DET":
                    if "ein" in t.text.lower():
                        object.append("einen")
                    else:
                        object.append("den")
                elif t.pos_ == "ADJ":
                    object.append(t.lemma_ + "en")
                elif t.pos_ == "NOUN":
                    if t.text[-1] == "e":
                        object.append(t.text + "n")
                    elif t.text[-3:] == "ent":
                        object.append(t.text + "en")
                else:
                    object.append(t.text)
            object = " ".join(object)
            return object
        else:
            object = " ".join([t.text for t in token.subtree])
            return object

    def correct_verb_suffix_present(self, morphology:list, verb:str):
        if "Person=1" not in morphology or "Person=2" not in morphology or "Person=3" not in morphology:
            morphology.append("Person=3")
        endT = False
        if verb[-1] == "t" or verb[-1] == "d":
            endT = True

        if "Number=Plur" in morphology and ("Person=1" in morphology or "Person=3" in morphology):
            return "en"
        elif ("Number=Plur" in morphology and "Person=2" in morphology) or ("Number=Sing" in morphology and "Person=3" in morphology):
            if endT:
                return "et"
            else:
                return "t"
        elif "Number=Sing" in morphology and "Person=2" in morphology:
            if endT:
                return "est"
            else:
                return "st"
        elif "Number=Sing" in morphology and "Person=1" in morphology:
            return "e"

    def find_root(self, token):
        if token.head.pos_ == "VERB" or token.head.pos_ == "AUX":
            return token.head
        else:
            return self.find_root(token.head)

    def ams_extend(self, nlp):
        """
        This rule extends ams words to their full form
        Regex-based
        """
        # changes /-separated words e.g. km/h to Kilometer pro Stunde
        search_result = re.finditer(r"\d+\s*(\w+\^*\d*\s*\/\s*\w+\^*\d*)(\W|$)", self.transformed_sentence.text)
        if search_result:
            for i in range(len(list(search_result))):
                search_result = re.finditer(r"\d+\s*(\w+\^*\d*\s*\/\s*\w+\^*\d*)(\W|$)", self.transformed_sentence.text)
                orig_sentence = self.transformed_sentence.text
                for match in search_result:
                    new_sentence = orig_sentence[:match.start(1)]
                    word_left, word_right = match.group(1).split("/")
                    try:
                        new_sentence += f"{rules.ams_regex_replace[word_left.strip()]} pro {rules.ams_regex_replace[word_right.strip()]}"
                        new_sentence += orig_sentence[match.end(1):]
                        self.transformed_sentence = nlp(new_sentence)
                    except KeyError:
                        continue
                    break

        matches = re.finditer(rules.ams_regex, self.transformed_sentence.text)

        to_replace = list()
        # extend the rest of the ams
        if matches:
            orig_sentence = self.transformed_sentence.text
            for match in matches:
                abbreviation = match.group(2)
                if abbreviation in rules.ams_regex_replace:
                    self.rules.append("AMS")
                    new_token = rules.ams_regex_replace[abbreviation]
                    oneWord = True
                    if len(new_token.split(" ")) > 1:
                        oneWord = False
                    for token in self.transformed_sentence:
                        if int(token.idx) <= int(match.start(2)) and int(match.end(2)) <= int(token.idx+len(token)):
                            ind = token.i
                    new_token = self.correct_to_case(self.transformed_sentence[ind], new_token, oneWord)
                    to_replace.append((match.start(2), match.end(2), new_token))

            new_sentence = ""
            prev_ind = 0
            for new in to_replace:
                new_sentence += orig_sentence[prev_ind:new[0]]
                new_sentence += new[2]
                if new[1] < len(orig_sentence)-1 and orig_sentence[new[1]] == ".":
                    prev_ind = new[1]+1
                else:
                    prev_ind = new[1]
            new_sentence += orig_sentence[prev_ind:]
            self.transformed_sentence = nlp(new_sentence.strip())

    def missing_ams_add(self, matcher, nlp):
        """
        This rule adds ams words to their full form
        Regex- and dependencies-based
        """
        # finds potential years
        matcher.add("AMS_MISSING", rules.ams_missing_rule)
        matches = matcher(self.transformed_sentence)
        extend_points = []

        if matches:
            for match in matches:
                span = self.transformed_sentence[match[1]:match[2]].text
                # check with the regex for years
                if re.search(rules.missing_ams_regex, span):
                    self.rules.append("AMS_MISSING")
                    # make sure it's not another 4-digit number by checking the verbs around
                    if self.transformed_sentence[match[1]].pos_ == "NUM":
                        extend_points.append(match[1])
                    elif self.transformed_sentence[match[1]].pos_ == "VERB" or self.transformed_sentence[match[1]].pos_ == "AUX":
                        extend_points.append(match[2]-1)

        new_sentence = [token.text if token.i not in extend_points else "im Jahr "+token.text for token in self.transformed_sentence]

        self.transformed_sentence = nlp(" ".join(new_sentence).strip())
        matcher.remove("AMS_MISSING")

    def coordination_split(self, matcher, nlp):
        #TODO: add handling of relative clauses (different sb)
        #TODO: add linking words for coherence e.g. Dann
        if len(self.transformed_sentence) > 23:
            matcher.add("COOR", rules.coordination_rule)
            matches = matcher(self.transformed_sentence)
            to_detach = list()
            to_remove = list()

            if matches:
                for match in matches:
                    try:
                        to_remove_local = list()
                        self.rules.append("COOR")
                        clause = []
                        cj = self.transformed_sentence[match[1]]
                        if cj.head.pos_ == "CCONJ":
                            to_remove_local.append(cj.head.i)
                            if cj.head.head.head.pos_ == "AUX":
                                root = cj.head.head.head
                            else:
                                root = cj.head.head
                        else:
                            if cj.head.head.pos_ == "AUX":
                                root = cj.head.head
                            else:
                                root = cj.head

                        # find subject, get full clause
                        sb = ""
                        root_morph = list(cj.morph)
                        sb_not_in_cj = False
                        for child in cj.children:
                            if child.dep_ == "sb":
                                sb = [token for token in child.subtree if token.pos_ != "ADJ"]
                                if child.lemma_ == "der":
                                    for ch in root.children:
                                        if ch.dep_ == "sb":
                                            sb = [token for token in ch.subtree if token.pos_ != "ADJ"]
                                            sb_not_in_cj = True
                                subtree = [token for token in cj.subtree if token not in sb]
                                if subtree[-1] == cj:
                                    subtree = subtree[:-1]
                                    subtree.insert(0, cj)
                                clause.extend(sb)
                                clause.extend(subtree)
                                if not sb_not_in_cj and sb:
                                    to_remove_local.extend(range(sb[0].i, sb[-1].i+1))
                                to_remove_local.extend(range(subtree[0].i, subtree[-1].i+1))
                        if not sb:
                            if "Number==Plur" in root_morph:
                                sb = ["Sie "]
                            else:
                                for child in root.children:
                                    if child.dep_ == "sb":
                                        sb = [child]
                                        if sb and sb[0].lemma_ == "der":
                                            for ch in sb[0].head.children:
                                                if ch.dep_ == "sb":
                                                    sb = [token for token in ch.subtree if token.pos_ != "ADJ"]
                                        else:
                                            sb = [token for token in sb[0].subtree if token.pos_ != "ADJ"]
                                        break
                            clause.extend(sb)
                            if root.pos_ == "AUX" and cj.pos_ != "AUX":
                                clause.append(root)
                                clause.extend(list(cj.subtree))
                                to_remove_local.extend(range(list(cj.subtree)[0].i, list(cj.subtree)[-1].i+1))
                            else:
                                subtree = list(cj.subtree)
                                if subtree[-1] == cj:
                                    subtree.insert(0, cj)
                                    subtree = subtree[:-1]
                                clause.extend(subtree)
                                to_remove_local.extend(range(subtree[0].i, subtree[-1].i+1))

                        new_clause = []
                        for token in clause:
                            try:
                                new_clause.append(token.text)
                            except:
                                new_clause.append(token)
                        new_clause_parsed = nlp(" ".join(new_clause) + ".")
                        if list(new_clause_parsed.sents)[0].root.pos_ != "AUX" and list(new_clause_parsed.sents)[0].root.pos_ != "VERB":
                            continue
                        else:
                            to_detach.append(" ".join(new_clause) + ".")
                            to_remove.extend(to_remove_local)
                    except:
                        continue

            if to_remove:
                for sent in to_detach:
                    self.detached_sentences.append(sent)
                new_sentence = [token.text for token in self.transformed_sentence if token.i not in to_remove]
                new_sentence = " ".join(new_sentence) + "."
                self.transformed_sentence = nlp(new_sentence)

            matcher.remove("COOR")

    def semicolon(self):
        """
        This rule detaches ;-separated clauses as separate sentences
        Regex- and dependencies-based
        """
        search_result = re.finditer(rules.semicolon_regex, self.transformed_sentence.text)
        indices = [0]
        if any(True for _ in search_result):
            for match in search_result:
                if match.group(1):
                    # check if the clause is full i.e. has a verb in it
                    prev_token_ind = 0
                    true_split = False
                    for token in self.transformed_sentence:
                        if token.idx == match.start(1):
                            prev_token_ind = token.i
                        for token in self.transformed_sentence[prev_token_ind:]:
                            if token.pos_ == "VERB" or token.pos_ == "AUX":
                                true_split = True
                    if true_split:
                        indices.append(match.start(1))
                        self.rules.append("SEMIC")
            # detach detected clauses
            if len(indices) > 1:
                orig_sentence = self.transformed_sentence.text
                new_sentences = [orig_sentence[i:j] for i, j in zip(indices, indices[1:]+[None])]
                for i in range(len(new_sentences)):
                    if new_sentences[i][0] == ";":
                        new_sentences[i] = new_sentences[i][1:]
                    new_sentences[i] = new_sentences[i].strip() + "."

                self.transformed_sentence = nlp(new_sentences[0])
                for i in range(1, len(new_sentences)):
                    self.detached_sentences.append(new_sentences[i])

    def passive_change(self, matcher, nlp):
        """
        This rule detaches passive clauses as separate sentences when the original sent is 17 words or longer
        Dependencies-based
        """
        #TODO: if passive in relative clause - detach
        matcher.add("PASS", rules.passive_rule)
        matches = matcher(self.transformed_sentence)
        if matches:
            if len(self.transformed_sentence) > 17:
                verbForms_file = open("utils/verbForms.json", encoding="utf-8")
                verbForms = json.load(verbForms_file)
                self.rules.append("PASS")
                to_remove = list()
                to_replace = defaultdict(tuple)
                modals = {"können":["kann", "kannst", "können", "könnt"],
                          "sollen":["soll", "sollst", "sollen", "sollt"],
                          "müssen":["muss", "musst", "müssen", "müsst"],
                          "wollen":["will", "willst", "wollen", "wollt"],
                          "dürfen":["darf", "darfst", "dürfen", "dürft"],
                          "mögen":["mag", "magst", "mögen", "mögt"]}
                matcher.remove("PASS")
                matcher.add("PART2", rules.partizip_2_rule)
                matcher.remove("PART2")

                # remove overlapping matches:
                matches_no_overlaps = []
                for match in matches:
                    if self.transformed_sentence[match[1]].head == self.transformed_sentence[match[2]-1]:
                        matches_no_overlaps.append(match)
                    elif self.transformed_sentence[match[2]-1].head == self.transformed_sentence[match[1]]:
                        matches_no_overlaps.append(match)
                matches_clean = list()
                matches_remove = list()
                for i in range(len(matches_no_overlaps)-1):
                    match1 = matches_no_overlaps[i]
                    for j in range(i+1, len(matches_no_overlaps)):
                        match2 = matches_no_overlaps[j]
                        if match1[1]==match2[1] or match1[2]-1==match2[2]-1 or match1[1]==match2[2]-1 or match1[2]-1==match2[1]:
                            dist1 = match1[2]-1-match1[1]
                            dist2 = match2[2]-1-match2[1]
                            if dist1 < dist2:
                                matches_remove.append(match2)
                            else:
                                matches_remove.append(match1)
                for match in matches_no_overlaps:
                    if match not in matches_remove:
                        matches_clean.append(match)

                # start passive handling
                for match in matches_clean:
                    try:
                        aux = ""
                        war = ""
                        modal = ""
                        hatte = ""
                        subordinated = False
                        reverse_wo = False
                        reverse_special = False
                        if self.transformed_sentence[match[1]].lemma_ == "werden":
                            aux = self.transformed_sentence[match[1]]
                        elif self.transformed_sentence[match[2]-1].lemma_ == "werden":
                            aux = self.transformed_sentence[match[2]-1]
                            if aux.head.lemma_ not in modals.keys():
                                if aux.head.lemma_ != "sein":
                                    subordinated = True
                                else:
                                    war = aux.head
                                    to_remove.append(war)
                                    if aux.head.i == match[2]:
                                        subordinated = True
                            elif aux.head.lemma_ in modals.keys():
                                modal = aux.head
                                if aux.head.head.lemma_ != "haben":
                                    if aux.head.i == match[2]:
                                        subordinated = True
                                else:
                                    hatte = aux.head.head
                                    to_remove.append(hatte)
                                    if aux.head.head.i == match[2]+1:
                                        subordinated = True

                        to_remove.append(aux)
                        if hatte:
                            base = hatte
                            subtree = list(hatte.subtree)
                        elif war:
                            base = war
                            subtree = list(war.subtree)
                        elif modal:
                            base = modal
                            subtree = list(modal.subtree)
                        else:
                            base = aux
                            subtree = list(aux.subtree)

                        object = ""
                        sb_pass = ""
                        sb_old = ""
                        predicates = []
                        for token in subtree:
                            if token.dep_ == "sb" and token.head == base and token.lemma_ == "der":
                                sb_old = token
                                if token.text == "das":
                                    object = "es"
                                elif token.text == "der":
                                    object = "ihn"
                                elif token.text == "die":
                                    object = "sie"
                            elif token.dep_ == "sb" and token.head == base:
                                sb_old = token
                                object = self.correct_to_accusative(token)
                                to_remove.extend(list(sb_old.subtree))
                                if sb_old.i > base.i:
                                    reverse_wo = True
                            elif token.dep_ == "sbp" and (token.head.i == match[1] or token.head.i == match[2]-1):
                                sb_pass = token
                                to_remove.extend(list(sb_pass.subtree))
                            elif token.pos_ == "VERB" and (token.i == match[1] or token.i == match[2]-1):
                                predicates.append(token)
                                if "cd" in [t.dep_ for t in token.children]:
                                    coord = True
                                    for t in token.subtree:
                                        if t != token:
                                            if (t.dep_ == "cd" or t.dep_ == "cj" or t.dep_ == "cc") and t.pos_ == "VERB":
                                                predicates.append(t)
                        if reverse_wo:
                            if sb_pass:
                                if not (sb_pass.i < base.i or predicates[0].i < base.i):
                                    reverse_special = True
                            else:
                                if not predicates[0].i < base.i:
                                    reverse_special = True

                        # PLACE SUBJECT (+OBJECT for subordinated)
                        object_placed = False
                        if sb_pass:
                            sb_new = [t for t in sb_pass.subtree if t != sb_pass]
                            sb_phrase = self.correct_to_nominative(list(sb_pass.children)[0], list(sb_pass.children)[0], sb_new, sbp=True)
                            if sb_old:
                                if subordinated or reverse_special:
                                    to_replace[sb_old.i] = (sb_pass, " ".join(sb_phrase) + " " + object, subordinated, reverse_wo)
                                    object_placed = True
                                else:
                                    to_replace[sb_old.i] = (sb_pass, " ".join(sb_phrase), subordinated, reverse_wo)
                            else:
                                if subordinated or reverse_special:
                                    to_replace["None"] = (aux, " ".join(sb_phrase) + " " + object, subordinated, reverse_wo)
                                    object_placed = True
                                else:
                                    to_replace["None"] = (aux, " ".join(sb_phrase), subordinated, reverse_wo)
                            for t in sb_pass.children:
                                features = list(t.morph)
                        else:
                            if sb_old:
                                if subordinated or reverse_special:
                                    to_replace[sb_old.i] = ("NEW", "man " + object, subordinated, reverse_wo)
                                    object_placed = True
                                else:
                                    to_replace[sb_old.i] = ("NEW", "man", subordinated, reverse_wo)
                            else:
                                if subordinated or reverse_special:
                                    to_replace["None"] = (aux, "man " + object, subordinated, reverse_wo)
                                    object_placed = True
                                else:
                                    to_replace["None"] = (aux, "man", subordinated, reverse_wo)
                            features = ["Number=Sing", "Person=3"]

                        if "Person=1" not in features or "Person=2" not in features or "Person=3" not in features:
                            features.append("Person=3")
                        if "Number=Sing" not in features or "Number=Plur" not in features:
                            features.append("Number=Sing")
                        #IMPERFEKT passive -> Praesense
                        if (aux.text[1] == "e" or aux.text[1] == "i") and not war and not hatte:
                            newForms_all = []
                            for predicate in predicates:
                                to_remove.append(predicate)
                                try:
                                    newForm = ""
                                    if modal:
                                        newForm = verbForms["PARTIZIP2toPRASENSE"][predicate.text][3].strip()
                                        if "Number=Sing" in features:
                                            if "Person=2" in features:
                                                new_modal = modals[modal.lemma_][1]
                                            else:
                                                new_modal = modals[modal.lemma_][0]
                                        elif "Number=Plur" in features:
                                            if "Person=2" in features:
                                                new_modal = modals[modal.lemma_][3]
                                            else:
                                                new_modal = modals[modal.lemma_][2]
                                    elif "Number=Sing" in features:
                                        if "Person=1" in features:
                                            newForm = verbForms["PARTIZIP2toPRASENSE"][predicate.text][0].strip()
                                        elif "Person=2" in features:
                                            newForm = verbForms["PARTIZIP2toPRASENSE"][predicate.text][1].strip()
                                        else:
                                            newForm = verbForms["PARTIZIP2toPRASENSE"][predicate.text][2].strip()
                                    elif "Number=Plur" in features:
                                        if "Person=1" in features:
                                            newForm = verbForms["PARTIZIP2toPRASENSE"][predicate.text][3].strip()
                                        elif "Person=2" in features:
                                            newForm = verbForms["PARTIZIP2toPRASENSE"][predicate.text][4].strip()
                                        else:
                                            newForm = verbForms["PARTIZIP2toPRASENSE"][predicate.text][3].strip()
                                    part = ''
                                    if " " in newForm:
                                        newForm, part = newForm.split()
                                    newForms_all.append((predicate, newForm, part))
                                except KeyError:
                                    part = ""
                                    try:
                                        ind = predicate.text.index("ge")
                                        part = predicate.text[:ind]
                                        newForm = predicate.lemma_.replace("ge", "")
                                        if part:
                                            newForm = newForm.replace(part, '')
                                        if newForm[-1] == "t":
                                            if modal:
                                                newForm += newForm[:-1] + self.correct_verb_suffix_present(["Number=Plur", "Person=1"], newForm)
                                            else:
                                                newForm += newForm[:-1] + self.correct_verb_suffix_present(features, newForm)
                                        else:
                                            newForm = "MISSINGFORM"
                                        newForms_all.append((predicate, newForm, part))
                                        if modal:
                                            if "Number=Sing" in features:
                                                if "Person=2" in features:
                                                    new_modal = modals[modal.lemma_][1]
                                                else:
                                                    new_modal = modals[modal.lemma_][0]
                                            elif "Number=Plur" in features:
                                                if "Person=2" in features:
                                                    new_modal = modals[modal.lemma_][3]
                                                else:
                                                    new_modal = modals[modal.lemma_][2]
                                    except ValueError:
                                        newForm = predicate.lemma_.replace("ge", "")
                                        if part:
                                            newForm = newForm.replace(part, '')

                                        if newForm[-1] == "t":
                                            if modal:
                                                newForm += newForm[:-1] + self.correct_verb_suffix_present(["Number=Plur", "Person=1"], newForm)
                                            else:
                                                newForm += newForm[:-1] + self.correct_verb_suffix_present(features, newForm)
                                        else:
                                            newForm = "MISSINGFORM"
                                        newForms_all.append((predicate, newForm, part))
                                        if modal:
                                            if "Number=Sing" in features:
                                                if "Person=2" in features:
                                                    new_modal = modals[modal.lemma_][1]
                                                else:
                                                    new_modal = modals[modal.lemma_][0]
                                            elif "Number=Plur" in features:
                                                if "Person=2" in features:
                                                    new_modal = modals[modal.lemma_][3]
                                                else:
                                                    new_modal = modals[modal.lemma_][2]

                            if sb_pass:
                                predicate_phrase = [t for t in newForms_all[0][0].subtree if t != newForms_all[0][0] and t not in sb_pass.subtree]
                            else:
                                predicate_phrase = [t for t in newForms_all[0][0].subtree if t != newForms_all[0][0]]
                            first_predicate = newForms_all[0]
                            if modal:
                                first_predicate = (first_predicate[0], first_predicate[2]+first_predicate[1], first_predicate[2])
                            if predicate_phrase:
                                pred_ind = predicate_phrase[0].i
                            if predicate_phrase:
                                indices = {token: i for i, token in enumerate(predicate_phrase)}
                                for newForm in newForms_all[1:]:
                                    ind = indices[newForm[0]]
                                    phrase_start_ind = indices[list(newForm[0].subtree)[0]]
                                    if not subordinated and not modal:
                                        predicate_phrase[ind] = newForm[2]
                                        predicate_phrase.insert(phrase_start_ind, newForm[1])
                                    else:
                                        predicate_phrase[ind]= newForm[2]+newForm[1]
                            predicate_phrase_full = ""
                            for token in predicate_phrase:
                                try:
                                    predicate_phrase_full += token.text + " "
                                    to_remove.append(token)
                                except:
                                    predicate_phrase_full += token + " "

                            if modal:
                                to_replace[modal.i] = (modal, new_modal, subordinated, reverse_wo)
                                to_remove.append(modal)
                            if predicate_phrase_full:
                                to_replace[pred_ind] = (pred_ind, first_predicate[2]+" "+predicate_phrase_full, subordinated, reverse_wo)
                            if base == aux and not subordinated:
                                if not object_placed:
                                    to_replace[aux.i] = (first_predicate[0], first_predicate[1]+" "+object, subordinated, reverse_wo, "MODAL", modal, "PARTICLE", first_predicate[2])
                                else:
                                    to_replace[aux.i] = (first_predicate[0], first_predicate[1], subordinated, reverse_wo, "MODAL", modal, "PARTICLE", first_predicate[2])
                            else:
                                if subordinated:
                                    to_replace[first_predicate[0].i] = (first_predicate[0], first_predicate[2]+first_predicate[1], subordinated, reverse_wo, "MODAL", modal)
                                else:
                                    if not object_placed:
                                        to_replace[first_predicate[0].i] = (first_predicate[0], object+" "+first_predicate[2]+first_predicate[1], subordinated, reverse_wo, "MODAL", modal)
                                    else:
                                        to_replace[first_predicate[0].i] = (first_predicate[0], first_predicate[2]+first_predicate[1], subordinated, reverse_wo, "MODAL", modal)

                        #PERFEKT passive -> Perfekt
                        elif aux.text[1] == "u" or (hatte and "tt" not in hatte.text):
                            haben = "hat"
                            if "Number=Sing" in features:
                                if "Person=1" in features:
                                    haben = "habe"
                                elif "Person=2" in features:
                                    haben = "hast"
                                else:
                                    haben = "hat"
                            elif "Number=Plur" in features:
                                if "Person=2" in features:
                                    haben = "habt"
                                else:
                                    haben = "haben"

                            if subordinated or reverse_special:
                                to_replace[base.i] = (base, haben, subordinated, reverse_wo, "MODAL", modal)
                            else:
                                to_replace[base.i] = (base, haben+" "+object, subordinated, reverse_wo, "MODAL", modal)

                        #PLUSQUAMPERFEKT passive -> Plusquamperfekt
                        elif (aux.text[1] == "o" and base.lemma_ == "sein") or (hatte and "tt" in hatte.text):
                            haben = "hatte"
                            if "Number=Sing" in features:
                                if "Person=2" in features:
                                    haben = "hattest"
                                else:
                                    haben = "hatte"
                            elif "Number=Plur" in features:
                                if "Person=2" in features:
                                    haben = "hattet"
                                else:
                                    haben = "hatten"

                            if subordinated or reverse_special:
                                to_replace[base.i] = (base, haben, subordinated, reverse_wo, "MODAL", modal)
                            else:
                                to_replace[base.i] = (base, haben+" "+object, subordinated, reverse_wo, "MODAL", modal)
                    except:
                        continue

                # PARTICLES in finite verbs
                if to_remove:
                    new_sentence = [t for t in self.transformed_sentence]
                    for token in to_replace:
                        if token != "None":
                            new_sentence[token] = to_replace[token][1]
                        else:
                            if token == "None":
                                if to_replace[token][0].head.lemma_ in modals.keys():
                                    new_sentence.insert(to_replace[token][0].head.i, to_replace[token][1])
                                else:
                                    if not to_replace[token][2]:
                                        new_sentence.insert(to_replace[token][0].i, to_replace[token][1])
                                    else:
                                        new_sentence.insert(to_replace[token][0].head.i+1, to_replace[token][1])
                    new_sentence_final = []
                    for token in new_sentence:
                        try:
                            if token not in to_remove:
                                new_sentence_final.append(token.text)
                        except TypeError:
                            new_sentence_final.append(token)

                    self.transformed_sentence = nlp(" ".join(new_sentence_final))

    def app_split(self, matcher, nlp):
        """
        This rule is not developed
        """
        #TODO:
        # extra 'e'; ?
        # article for subject must be defined by subject's morphology! see validation "Mit einer seit Jahrhunderten bestehenden Staustufe"
        matcher.add("APP", rules.app_split_rule)
        matches = matcher(self.transformed_sentence)
        if matches:
            for m in range(len(matches)):
                try:
                    matches = matcher(self.transformed_sentence)
                    wrong_parse = False
                    app_root = self.transformed_sentence[matches[0][1]]
                    app_phrase = [token for token in app_root.subtree]
                    app_is_proper = True
                    for token in app_phrase:
                        if token.pos_ != "PROPN" and token.pos_ != "DET":
                            app_is_proper = False
                    # not APP if next or previous are cjs
                    dep_order = []
                    try:
                        root_children = list(self.find_root(app_root).children)
                        for child in root_children:
                            if child.dep_ == "cj":
                                dep_order.extend([tok.i for tok in child.subtree])
                        if app_phrase[0].i-2 in dep_order or app_phrase[-1].i+2 in dep_order:
                            wrong_parse = True
                    except RecursionError:
                        wrong_parse = True

                    if not wrong_parse:
                        # if z.B in appositonal phrase don't detach
                        not_split = re.search(rules.app_not_split_regex, " ".join([t.text for t in app_phrase]))
                        if not not_split:
                            if self.transformed_sentence[app_phrase[0].i-1].text == "," and self.transformed_sentence[app_phrase[-1].i+1].text == ",":
                                self.rules.append("APP")
                                orig_sentence = self.transformed_sentence.text
                                new_sentence = orig_sentence[:app_phrase[0].idx].strip()
                                if self.transformed_sentence[app_phrase[-1].i+2].pos_ == "VERB" or self.transformed_sentence[app_phrase[-1].i+2].pos_ == "AUX":
                                    new_sentence = new_sentence.strip(",")
                                #sentence_left = new_sentence + " " + orig_sentence[app_phrase[-1].idx+len(app_phrase[-1])+1:].strip()
                                #if self.transformed_sentence[app_phrase[-1].i+2].dep_ != "rc" and self.transformed_sentence[app_phrase[-1].i+2].dep_ != "cp":
                                sentence_left = new_sentence + " " + orig_sentence[app_phrase[-1].idx+len(app_phrase[-1])+1:].strip()
                                #else:
                                 #   sentence_left = new_sentence + " " + orig_sentence[app_phrase[-1].idx+len(app_phrase[-1]):].strip()
                                self.transformed_sentence = nlp(sentence_left)
                                #self.update_transformed()

                                #morphology = list(app_root.morph)
                                app_parent = app_root.head
                                is_proper = False
                                app_noun_phrase_right = list(self.transformed_sentence[app_parent.i].rights)
                                app_noun_phrase_left = list(self.transformed_sentence[app_parent.i].lefts)
                                app_noun_phrase_right = [token for token in app_noun_phrase_right if token.i < app_phrase[0].i and (token.pos_ != "NUM" and token.pos_ != "ADJ")] #and (token.pos_ == "PROPN" or token.pos_ == "NOUN")]
                                app_noun_phrase_left = [token for token in app_noun_phrase_left if (token.pos_ != "ADJ" and token.pos_ != "DET" and token.pos_ != "ADV")] #if token.pos_ == "PROPN" or token.pos_ == "NOUN"]
                                app_parent_phrase = []
                                for token in app_noun_phrase_left:
                                    app_parent_phrase.append(token)
                                    if token.pos_ == "PROPN":
                                        is_proper = True
                                app_parent_phrase.append(app_parent)
                                if app_parent.pos_ == "PROPN":
                                    is_proper = True
                                for token in app_noun_phrase_right:
                                    app_parent_phrase.append(token)
                                    #if token.pos_ == "PROPN":
                                     #   is_proper = True

                                morphology = list(app_parent.morph)
                                sents = [s for s in self.transformed_sentence.sents]
                                morph_root = list(sents[0].root.morph)
                                sentence_right = ""
                                app_parent_phrase = self.correct_to_nominative(app_parent, app_parent, app_parent_phrase)
                                if not is_proper:
                                    if "Gender=Neut" in morphology and "Number=Sing" in morphology:
                                        sentence_right += "Das " + " ".join(app_parent_phrase) + " "
                                    elif "Gender=Masc" in morphology and "Number=Sing" in morphology:
                                        sentence_right += "Der " + " ".join(app_parent_phrase) + " "
                                    else:
                                        sentence_right += "Die " + " ".join(app_parent_phrase) + " "
                                else:
                                    sentence_right += " ".join(app_parent_phrase) + " "
                                    sentence_right = sentence_right[0].upper() + sentence_right[1:]
                                sentence_right = sentence_right.strip().strip(",")

                                if "Tense=Past" in morph_root:
                                    if "Number=Sing" in morphology:
                                        if app_is_proper:
                                            sentence_right += " hieß "
                                        else:
                                            sentence_right += " war "
                                    else:
                                        if app_is_proper:
                                            sentence_right += " hießen "
                                        else:
                                            sentence_right += " waren "
                                else:
                                    if "Number=Sing" in morphology:
                                        if app_is_proper:
                                            sentence_right += " heißt "
                                        else:
                                            sentence_right += " ist "
                                    else:
                                        if app_is_proper:
                                            sentence_right += " heißen "
                                        else:
                                            sentence_right += " sind "

                                #print(sentence_right)
                                app_phrase = self.correct_to_nominative(app_root, app_parent, app_phrase)
                                #print(app_phrase)
                                sentence_right += " ".join(app_phrase) + "."
                                #print(sentence_right)
                                #self.transformed_sentence = nlp(sentence_left)
                                #self.update_transformed()
                                self.detached_sentences.append(sentence_right)

                except IndexError:
                    continue

        matcher.remove("APP")

    def partic_modif_transform(self, nlp):
        """
        This rule is not developed
        """
        #TODO: messy output
        #TODO: add passive if accusative
        #TODO: check if parent_right is "von" or noun or propn, if not attach the relative clause if yes, attach after the phrase/word
        new_sentence = ""
        verbForms_file = open("utils/verbForms.json", encoding="utf-8")
        verbForms = json.load(verbForms_file)
        part_modif = set()
        pattern_p1 = r"(lnde$|ende$|lnden$|enden$)"
        pattern_p2 = r"((ge)+\w+(ene$)+|(ge)+\w+(enen$)+|(ge)+\w+(te$)+|(ge)+\w+(ten$)+|ierte$|ierten$)"

        for token in self.transformed_sentence:
            if token.pos_ == "NOUN" or token.pos_ == "PROPN":
                noun_phrase = [tok for tok in token.subtree]
                for word in noun_phrase:
                    if word.pos_ == "ADJ":
                        if re.search(pattern_p1, word.text) and len(list(word.subtree)) > 1:
                            part_modif.add((word, "PARTIZIP1toPRASENSE"))
                        elif re.search(pattern_p2, word.text) and len(list(word.subtree)) > 1:
                            part_modif.add((word, "PARTIZIP2toPRATERITUM"))

        for token in part_modif:
            modif_phrase = list(token[0].subtree)
            new_sentence = [tok for tok in self.transformed_sentence if tok not in modif_phrase]
            part_parent = token[0].head
            parent_phrase = list(part_parent.subtree)
            features = list(part_parent.morph)

            if "Number=Sing" in features:
                if "Gender=Masc" in features:
                    #print(self.transformed_sentence)
                    #print(parent_phrase)
                    #print(new_sentence)
                    new_sentence.insert(parent_phrase[-1].i-1, ", der ")
                    #print(new_sentence)
                elif "Gender=Neut" in features:
                    new_sentence.insert(parent_phrase[-1].i+1, ", das ")
                elif "Gender=Fem" in features:
                    new_sentence.insert(parent_phrase[-1].i+1, ", die ")

                new_sentence.insert(parent_phrase[-1].i+2, " ".join([tok.text for tok in modif_phrase if tok != token[0]]))
                try:
                    newForm = verbForms[token[1]][token[0].lemma_][2].strip()
                except KeyError:
                    if token[1] == "PARTIZIP1toPRASENSE":
                        newForm = token[0].lemma_[:-1]
                    else:
                        newForm = token[0].lemma_.replace("ge", "")
                        if newForm[-1] == "t":
                            newForm += "e"
                if " " in newForm:
                    verb, part = newForm.split()
                    newForm = part + verb
                new_sentence.insert(parent_phrase[-1].i+3, " " + newForm + ",")
            elif "Number=Plur" in features:
                new_sentence.insert(parent_phrase[-1].i+1, ", die " + " ".join([token.text for token in modif_phrase[:-1]]))
                new_sentence.insert(parent_phrase[-1].i+2, " ".join([tok.text for tok in modif_phrase if tok != token[0]]))
                try:
                    newForm = verbForms[token[1]][token[0].lemma_][3].strip()
                    if " " in newForm:
                        verb, part = newForm.split()
                        newForm = part + verb
                except KeyError:
                    if token[1] == "PARTIZIP1toPRASENSE":
                        newForm = token[0].lemma_[:-1]
                    else:
                        newForm = token[0].lemma_.replace("ge", "")
                        if newForm[-1] == "t":
                            newForm += "en"
                new_sentence.insert(parent_phrase[-1].i+3, " " + newForm + ",")

            for ind in range(len(new_sentence)):
                try:
                    new_sentence[ind] = new_sentence[ind].text
                except:
                    continue
            new_sentence = " ".join(new_sentence)
            #print(new_sentence)
            self.transformed_sentence = nlp(new_sentence)
            #self.update_transformed()

            #TODO: right grammar form of the participle: CHECK OUTPUT


if __name__ == '__main__':
    """
    This module performs rule-based syntactic simplification.
    Input: data file with IDs, original and target texts
    Output: data file with IDs and simplified texts
    """

    nlp = spacy.load("de_core_news_lg")
    matcher = Matcher(nlp.vocab)
    data_path = sys.argv[1]
    ind = data_path.index(".")
    transformed_corpus_path = data_path[:ind] + "_simplified.txt"
    transformed_corpus = open(transformed_corpus_path, "w", encoding="utf-8")

    if data_path[-3:] == "txt":
        with open(data_path, "r", encoding="utf-8") as f:
            line_number = 0
            line = f.readline().strip()
            id = 0
            while line:
                line_number += 1
                try:
                    if "###ID###" in line:
                        line = f.readline().strip()
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
                        sentences = []
                        parsed_doc = nlp(doc)
                        for parsed_sent in parsed_doc:
                            sentence = Simplifier(parsed_sent)
                            if len(parsed_sent) > 0:
                                sentence.ams_extend(nlp)
                                sentence.missing_ams_add(matcher, nlp)
                                sentence.semicolon()
                                #sentence.partic_modif_transform(nlp)
                                #sentence.app_split(matcher, nlp)
                                sentence.coordination_split(matcher, nlp)
                                sentence.passive_change(matcher, nlp)

                                """ FOR SEPARATE RULE TESTING
                                RULES SET: PASS, SEMIC, AMS_MISSING, AMS, COOR """
                                #if "PASS" in sentence.rules:
                                  #  print(f"ORIGINAL: {sent}")
                                   # print(f"TRANSFOR: {sentence.transformed_sentence.text} {sentence.detached_sentences}")

                                sentences.append(sentence)

                        # compile transformed text
                        new_text = ""
                        for sent in sentences:
                            text = sent.transformed_sentence.text.strip()[0].upper() + sent.transformed_sentence.text.strip()[1:] + " "
                            new_text += normalize_punct(text) + " "
                            for s in sent.detached_sentences:
                                s = s.strip()[0].upper() + s.strip()[1:]
                                s = normalize_punct(s)
                                new_text += s + " "

                        # write in the output file
                        transformed_corpus.write("###ID###\n")
                        transformed_corpus.write(f"###{str(id)}###\n")
                        transformed_corpus.write("###SIMP###\n")
                        transformed_corpus.write(new_text + "\n")

                    elif "###TARG###" in line:
                        target_text = ''
                        while line:
                            line = f.readline().strip()
                            if line and "###ID###" not in line:
                                line_number += 1
                                target_text += line
                            else:
                                break

                except KeyError:
                    print(f"Invalid data file structure or formatting in line {line_number}. \nSee README to comply with data file requirements.")

    elif data_path[-5:] == "jsonl":
        with jsonlines.open(data_path) as f:
            line = 0
            for doc in f:
                line += 1
                try:
                    sentences = []
                    for sent in doc["wiki_sentences"]:
                        parsed_sent = nlp(sent)
                        sentence = Simplifier(parsed_sent)
                        if len(parsed_sent) > 0:
                            sentence.ams_extend(nlp)
                            sentence.missing_ams_add(matcher, nlp)
                            sentence.semicolon()  # has detached sents
                            detached_sents = list() # all semicolon-split sentence parts
                            for detached_s in sentence.detached_sentences:
                                parsed_detached_s = nlp(detached_s)
                                sentence_detached_s = Simplifier(parsed_detached_s)
                                detached_sents.append(sentence_detached_s)
                            sentence.detached_sentences = []

                            sentence.coordination_split(matcher, nlp) # has new detached sents
                            # for every sent in detached list apply coordination rule
                            detahced_sents_coord = list() # all semic + coord split sentence parts
                            for s in detached_sents:
                                s.coordination_split(matcher, nlp)
                                detahced_sents_coord.append(s)
                                for ds in s.detached_sentences:
                                    parsed_detached_ds = nlp(ds)
                                    sentence_detached_ds = Simplifier(parsed_detached_ds)
                                    detahced_sents_coord.append(sentence_detached_ds)
                                s.detached_sentences = []

                            sentence.passive_change(matcher, nlp)
                            # for every sent in detached list apply passive rule
                            for s in detahced_sents_coord:
                                s.passive_change(matcher, nlp)

                            #sentence.partic_modif_transform(nlp)
                            #sentence.app_split(matcher, nlp)

                            """ FOR SEPARATE RULE TESTING
                            RULES SET: PASS, SEMIC, AMS_MISSING, AMS, COOR """
                            #if "PASS" in sentence.rules:
                              #  print(f"ORIGINAL: {sent}")
                               # print(f"TRANSFOR: {sentence.transformed_sentence.text} {sentence.detached_sentences}")

                            # append sentences in the correct order
                            sentences.append(sentence)
                            sentences.extend(detahced_sents_coord)

                    # compile transformed text
                    new_text = ""
                    for sent in sentences:
                        text = sent.transformed_sentence.text.strip()[0].upper() + sent.transformed_sentence.text.strip()[1:] + " "
                        new_text += normalize_punct(text) + " "
                        for s in sent.detached_sentences:
                            s = s.strip()[0].upper() + s.strip()[1:]
                            s = normalize_punct(s)
                            new_text += s + " "

                    # write in the output file
                    transformed_corpus.write("###ID###\n")
                    transformed_corpus.write(f"###{str(doc['u_id'])}###\n")
                    transformed_corpus.write("###SIMP###\n")
                    transformed_corpus.write(new_text + "\n")

                except KeyError:
                    print(f"Invalid data file structure or formatting in line {line}. \nSee README to comply with data file requirements.")

    else:
        raise Exception("Invalid data file format. \nUse txt or jsonl files.")
