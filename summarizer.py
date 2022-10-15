from multilang_summarizer.summarizer import summarizer
from multilang_summarizer.lemmatizer import Lemmatizer
from multilang_summarizer.summarizer import summary_wordlimit
from multilang_summarizer.summarizer import clean_working_memory
import sys
import jsonlines


class Summarizer:
    def __init__(self):
        """
        Initalizes summarizer with a Klexikon average text length
        """
        self.lemmatizer = Lemmatizer.for_language("de")
        self.word_limit = 436

    def do_summary(self, input_text):
        clean_working_memory()
        file_path = "summaries/text1.txt"
        with open(file_path, "w", encoding="utf-8") as inF:
            inF.write(input_text)

        _, res2 = summarizer(file_path, f_method='f2', seq_method="partial", lemmatizer=self.lemmatizer, session_id=1)
        _, res2 = summarizer(file_path, f_method='f2', seq_method="partial", lemmatizer=self.lemmatizer, session_id=1)

        # ADD YOUR ACTUAL PATH
        with open("./multilang_summarizer/data/temp/running_summary_1.txt", "r", encoding="utf-8") as f:
            text = f.readlines()
            summary_final = summary_wordlimit(text, res2, word_limit=self.word_limit)

        return summary_final


if __name__ == "__main__":
    """
    This module performs summarization of original German texts. 
    Needs a data file path as input.
    """
    summarizer1 = Summarizer()
    data_path = sys.argv[1]
    ind = data_path.index(".")
    transformed_corpus_path = data_path[:ind] + "_summarized.txt"
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
                        line = line.replace("#", "", 6)
                        id = int(line)
                        line_number += 1
                        line = f.readline().strip()
                    elif "###ORIG###" in line or "###SIMP###":
                        doc = ''
                        while line:
                            line = f.readline().strip()
                            if line and "###TARG###" not in line and "###ID###" not in line:
                                line_number += 1
                                doc += line
                            else:
                                break

                        summary = " ".join(summarizer1.do_summary(doc))
                        # write in the output file
                        transformed_corpus.write("###ID###\n")
                        transformed_corpus.write(f"###{str(id)}###\n")
                        transformed_corpus.write("###SUMM###\n")
                        transformed_corpus.write(summary + "\n")

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

            print("Finished summarizing.")

    elif data_path[-5:] == "jsonl":
        with jsonlines.open(data_path) as f:
            line = 0
            for doc in f:
                line += 1
                try:
                    summary = " ".join(summarizer1.do_summary(" ".join(doc['wiki_sentences'])))

                    # write in the output file
                    transformed_corpus.write("###ID###\n")
                    transformed_corpus.write(f"###{str(doc['u_id'])}###\n")
                    transformed_corpus.write("###SUMM###\n")
                    transformed_corpus.write(summary + "\n")

                except KeyError:
                    print(f"Invalid data file structure or formatting in line {line}. \nSee README to comply with data file requirements.")
            print("Finished summarizing.")

    else:
        raise Exception("Invalid data file format. \nUse txt or jsonl files.")

