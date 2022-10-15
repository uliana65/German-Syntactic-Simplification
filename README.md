# Syntactic Simplification for German

###Purpose:
This project intends to perform syntactic simplification of German texts to make them more readable for children of the age of 8-12. 
The rewrite rules are motivated by the syntactic structure of the original German texts targeted at children of this age.

###Use

####Prepare data files:
Use 2 file formats: _txt_ or _jsonl_
1. Structure of a _txt_ file:
    
    Each text document should include a unique id, original text, and its target simplified version.
    These parts should be separated by "###ID###", "###ORIG###", "###TARG###" tags respectively on a separate line before the content.
    Refer to the `data_file_example.txt` for an example file structure and formatting.


2. Structure of a _jsonl_ file:

    Each jsonl line should include a dictionary with "u_id", "wiki_sentences", and "klexikon_sentences" entries.
    The "u_id" field is a unique document id. The "wiki_sentences" is a list of sentences of the original text. The "klexikon_sentences" is a list of sentences of the target text. 
    Each sentence in should appear separately in the list. Refer to the `klexikon.jsonl` file for an example. 

####Simplify:
Use this command to run syntactic simplification on your file:

`python syntactic_simplifier.py path_to_your_data_file`

This will write a new _simplified.txt_ file with simplified texts under the same ID as the original ones.

####Summarize:
Change the file path in the `summarizer.py` file, line 27 to where your multilang_summarizer is located (keep the path from "/multilang_summarizer/data/temp/running_summary_1.txt").
Use this command to run summarization on your _jsonl_ file or the _simplified.txt_ file:

`python summarizer.py path_to_your_data_file`

This will write a new _summarized.txt_ file with summarized texts under the same ID as the input ones.

####Evaluate:
Use this command to perform evaluation on your _jsonl_ file or _txt_ file:

`python evaluate.py path_to_your_original_file path_to_your_simplified/summarized_file`

This will provide Flesch scores for each of the corpora and plot their syntactic distributions.

####Acknoledgements:
This project makes use of German verb conjugation dictionary from the Pattern library compiled by Andreas Motl (https://gist.github.com/amotl/ad5ecda4579ad60bb6497b7ddabc8ad0). The summarization is performed by the Multilang Summarizer developed by Arturo Curiel. Thanks to them for their work! 
