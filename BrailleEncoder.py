import pandas as pd
import re


class BrailleEncoder:
    def __init__(self):
        df = pd.read_csv("./braille_characters.csv").drop(['formula'], axis=1)

        # create map of word/braille chars from df
        self.codex = {}
        for label in df['class'].unique():
            temp_df = df.loc[df['class'] == label].drop(['class'], axis=1)
            temp_dict = {label: temp_df.groupby(['key']).apply(lambda x: x['value'].tolist()[0]).to_dict()}
            self.codex.update(temp_dict)
        self.codex.keys()

        # prefixes and suffixes added to text: indicates capital, lower, number
        indicators = ['indicators']
        self.indicators_dict = self.select_keys(indicators, self.codex)

        # Grade 2: whole words (if separated by spaces (or hyphens?))
        word_signs = [
            # highest priority
            'shortform_words',
            # second highest priority
            'strong_wordsigns',
            # third highest priority
            'alphabetic_wordsigns',
            # lowest priority words
            'lower_wordsigns']
        self.word_signs_dict = self.select_keys(word_signs, self.codex)
        self.word_signs_dict = self.reorder_dict(word_signs, self.word_signs_dict)

        # Grade 2: mid word contractions
        contractions = [  # first priority: do these first because they might include the following signs
            'initial_letter_contractions', 'final_letter_groupsigns',
            # second priority: do these next
            'strong_contractions', 'strong_groupsigns',
            # lowest priority: do these last
            'middle_word_groupsigns', 'lower_groupsigns']
        self.contractions_dict = self.select_keys(contractions, self.codex)
        self.contractions_dict = self.reorder_dict(contractions, self.contractions_dict)

        # Grade 1: alphanumeric and punctuation charaters
        alphanum = ['alphabet', 'numbers', 'punctuation']
        self.alphanum_dict = self.select_keys(alphanum, self.codex)
        self.alphanum_dict = self.reorder_dict(alphanum, self.alphanum_dict)

    def reorder_dict(self, desired_keys, input_dict):
        # match order
        return {k: input_dict[k] for k in desired_keys}

    def select_keys(self, desired_keys, input_dict):
        # remove keys other than desired
        return {your_key: input_dict[your_key] for your_key in desired_keys}

    def get_contractions(self, chars):
        return sorted([chars[index: index + length] for index in range(len(chars) - 1) for length in
                       range(2, len(chars) - index + 1)], key=len, reverse=True)

    def nth_repl(self, s, sub, repl, n):
        find = s.find(sub)
        # If find is not -1 we have found at least one match for the substring
        i = find != -1
        # loop util we find the nth or we find no match
        while find != -1 and i != n:
            # find + 1 means we start searching from after the last match
            find = s.find(sub, find + 1)
            i += 1
        # If i is equal to n we found nth match so replace
        if i == n:
            return s[:find] + repl + s[find + len(sub):]
        return s

    def encode_word(self, word):
        # encode whole words
        for word_type in self.word_signs_dict.keys():
            for word_key in self.word_signs_dict[word_type].keys():
                if word == word_key:
                    return self.word_signs_dict[word_type][word_key]

        # encode contractions
        word_chars = word
        contractions = self.get_contractions(word_chars)
        for contraction_type in self.contractions_dict.keys():

            # loop through contractions in codex
            for contraction_key in self.contractions_dict[contraction_type].keys():

                # loop through contractions in word
                for word_segment in contractions:

                    if word_segment == contraction_key:

                        if contraction_type == 'initial_letter_contractions' and not (
                        word.startswith(contraction_key)) and word.startswith(" " + contraction_key):
                            # if not start of word, skip this word segment
                            break
                        elif contraction_type == 'final_letter_groupsigns':
                            if word.endswith(contraction_key) and not word.endswith(" " + contraction_key):
                                # replace last instance
                                word_chars = self.nth_repl(
                                    word_chars[::-1],
                                    contraction_key[::-1],
                                    self.contractions_dict[contraction_type][contraction_key][::-1],
                                    1
                                )[::-1]
                                # remove used chars from string
                                contractions = self.get_contractions(
                                    self.nth_repl(
                                        word_chars[::-1],
                                        contraction_key[::-1],
                                        "", 1)
                                )[::-1]
                            else:
                                break
                        elif contraction_type == 'middle_word_groupsigns':
                            # if the word segment is the whole word, skip this contraction type
                            if word_segment == word:
                                break
                            # if the word starts with this contraction, replace the second occurance of this contraction
                            index = 1
                            if word.startswith(contraction_key):
                                index += 1
                            # replace first instance
                            word_chars = self.nth_repl(
                                word_chars,
                                contraction_key,
                                self.contractions_dict[contraction_type][contraction_key],
                                index
                            )
                            # remove used chars from string
                            contractions = self.get_contractions(
                                self.nth_repl(
                                    word_chars,
                                    contraction_key,
                                    "",
                                    index
                                )
                            )
                        else:
                            # replace first instance
                            word_chars = self.nth_repl(
                                word_chars,
                                contraction_key,
                                self.contractions_dict[contraction_type][contraction_key],
                                1
                            )
                            # remove used chars from string
                            contractions = self.get_contractions(self.nth_repl(word_chars, contraction_key, "", 1))
                        break

        # encode individual chars
        for char in word_chars:
            for char_type in self.alphanum_dict.keys():
                for char_key in self.alphanum_dict[char_type].keys():
                    if char == char_key:
                        word_chars = word_chars.replace(char, self.alphanum_dict[char_type][char_key], 1)

        return word_chars

    def encode_text(self, sentence):
        words = re.findall(r"\w+|[^\w\s]", sentence, re.UNICODE)

        encoded_words = []
        new_sentence = []

        # if sentence is upper case
        if " ".join(words).isupper():
            for i in range(len(words)):
                encoded_words.append(self.encode_word(words[i].lower()))
                if i == 0:
                    new_sentence.append(self.indicators_dict['indicators']['capital_passage'] + words[i])
                else:
                    new_sentence.append(words[i])

        else:

            for i in range(len(words)):

                encoded_words.append(self.encode_word(words[i].lower()))

                # if word is numeric
                if words[i].isnumeric():
                    new_word = self.indicators_dict['indicators']['numeric'] + words[i]
                    new_sentence.append(new_word)

                # if word is upper case
                elif words[i].isupper():
                    new_word = self.indicators_dict['indicators']['capital_word'] + words[i]
                    new_sentence.append(new_word)

                else:

                    temp_word = ""

                    # add indicators letter by letter
                    for j in range(len(words[i])):

                        # if first letter of word is capitalised
                        if j == 0 and words[i][j].isupper():
                            temp_word += self.indicators_dict['indicators']['capital_letter'] + words[i][j]

                        # # mid word capitals
                        # elif words[i][j].isupper():
                        #   temp_word += indicators_dict['indicators']['capital_letter']+ words[i][j]

                        # individual numbers
                        elif words[i][j].isnumeric():
                            temp_word += self.indicators_dict['indicators']['numeric'] + words[i][j]

                        # just copy the letter over as is
                        else:
                            temp_word += words[i][j]

                    new_sentence.append(temp_word)

        # mapped_words = dict(zip(words, encoded_words))
        encoded_sentence = []
        for i in range(len(new_sentence)):
            encoded_sentence.append(self.nth_repl(new_sentence[i], words[i], encoded_words[i], 1))


        encoded_sentence = " ".join(encoded_sentence)

        # remove spaces before period
        period = self.alphanum_dict['punctuation']["."]
        encoded_sentence = encoded_sentence.replace(" " + period, period)

        # remove spaces before colon
        colon = self.alphanum_dict['punctuation'][":"]
        encoded_sentence = encoded_sentence.replace(" " + colon, colon)

        # remove spaces before and after hyphen
        hyphen = self.alphanum_dict['punctuation']["-"]
        encoded_sentence = encoded_sentence.replace(" " + hyphen + " ", hyphen)

        return encoded_sentence

# be = BrailleEncoder()
# print(be.encode_text("English to Braille Transcriber"))
# print(be.encode_text("ALL CAPS SENTENCE"))
# print(be.encode_text("child"))
# print(be.encode_text("c h i l d"))