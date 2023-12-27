# encoding=utf-8
from __future__ import print_function, unicode_literals
import csv
import json
import sys
import re
from json import dumps, dump
import spacy
import ast

sys.path.append("../")

input_file = './a1.txt'
dict_out_file = './a1.json'
dict_file = './dictionnaire.txt'
segment_file = './rule_segment.txt'
syntax_file = './rule_syntax.txt'
tag_text = './parser_result.txt'
EPL_info_file = './EPL_info.txt'


class annotate_text:
    def __init__(self):
        self.tag_table_total = []

    # lire le texte ligne par ligne et renvoyer les phrases
    def read_text(self, file):
        with open(file, encoding='utf-8') as f:
            phrases = f.readlines()
            return phrases

    def read_dict(self):
        """
        Lire le fichier dictionnaire.txt, sauvegarder les mots-clés et les étiquettes en paires clé-valeur.

        """
        with open(dict_file, 'r', encoding='utf-8') as f:
            tags_info = f.readlines()
            dict_tag_info = {}
            for word_tag_info in tags_info:
                try:
                    dict_info = word_tag_info.strip('\n').split(',')
                    dict_tag_info[dict_info[0]] = dict_info[1]
                except:
                    print('Erreur de lecture du dictionnaire:', word_tag_info)

            return dict_tag_info

    def lemmatisation(self, text):
        try:
            import spacy
        except ImportError:
            print("Impossible d'importer le module nécessaire spacy !")
            return
        # Charger le modèle de langue
        try:
            nlp = spacy.load("fr_core_news_lg")
        except Exception as err:
            spacy.cli.download("fr_core_news_lg")
            nlp = spacy.load("fr_core_news_lg")
        # Appeler Spacy pour effectuer la lemmatisation et la tokenisation du texte.
        doc = nlp(text)
        sents_dict = {}
        for sent in doc.sents:
            if sent not in sents_dict:
                tokens_formes = [[], []]
                for i, token in enumerate(sent):
                    tokens_formes[1].append(token.text)
                    tokens_formes[0].append(token.lemma_)
                    sents_dict[sent.text] = tokens_formes
        # Renvoyer les résultats de l'analyse de Spacy.
        return sents_dict

    def cut_sentence(self, sentence, sentence_seg):
        """
        Effectuer une segmentation précise de la phrase en utilisant rule_segment.txt

        """

        annotate_text_info = []
        # lire le fichier rule.segment.txt
        items = {"rule_info": []}
        with open(segment_file, encoding='utf-8') as f:
            rule_segment = f.readlines()
        # Si les mots ne sont pas correctement segmentés,
        # utilisez le code suivant pour diviser les mots en plusieurs
        # parties. Le code de ce projet n'inclut pas cette section,
        # mais pour maintenir l'intégrité du script,  # elle est conservée.

        words = sentence_seg[0]
        list_words = []
        for word in words:
            seg_word = []
            for rule in rule_segment:
                if rule[0] != '/':
                    rule_info = rule.strip('\n').split(',')
                    if rule_info[0] == 'segment':
                        if word == rule_info[1]:
                            word_ = rule_info[2].split('+')

                            for small_word in word_:
                                seg_word.append(small_word)
                                items['rule_info'].append({'expr': small_word, 'rule': rule})

            if not seg_word:
                list_words.append(word)
            else:
                for small_word in seg_word:
                    list_words.append(small_word)

        # Consulter les règles de combiner les mot et effectuer la composition
        # Parcourir chaque mot dans la phrase.
        for index_word, word in enumerate(list_words):
            for rule in rule_segment:
                if rule[0] != '/':
                    rule_info = rule.strip('\n').split(',')
                    if rule_info[0] == 'combine':

                        combine_info = rule_info[1].split('+')
                        # Si le premier mot de la phrase correspond au premier mot dans les règles.
                        if word == combine_info[0]:
                            find_combine_value = []
                            find_combine_index = []
                            # Parcourir chaque mot des règles de composition des mots
                            for index_seg, seg_info in enumerate(combine_info):
                                # Après avoir trouvé le premier mot, chercher les mots suivants dans la phrase."
                                if index_word + index_seg < len(list_words):
                                    if seg_info == list_words[index_word + index_seg]:
                                        find_combine_value.append(seg_info)
                                        find_combine_index.append(index_word + index_seg)
                            expr = ' '.join(find_combine_value)
                            # Si le groupe de mots trouvé dans la phrase correspond
                            # au groupe de mots souhaité selon les règles.
                            if expr == rule_info[2]:

                                expr_orig = ' '.join(
                                    sentence_seg[1][find_combine_index[0]:find_combine_index[-1] + 1])
                                # Supprimer les mots d'origine, mettre à jour la phrase avec les mots combinés.
                                for index_combine in find_combine_index:
                                    del list_words[find_combine_index[0]]
                                    del sentence_seg[1][find_combine_index[0]]
                                list_words.insert(find_combine_index[0], expr)
                                sentence_seg[1].insert(find_combine_index[0], expr_orig)
                                # Enregistrer les mots combinés et les règles de composition exécutées
                                items['rule_info'].append({'expr': expr, 'rule': rule})
        items['seg_phrase'] = list_words
        items['seg_phrase_original'] = sentence_seg[1]
        items['phrase_original'] = sentence
        annotate_text_info.append(items)
        # Stocker les mots et les listes d'étiquettes correspondantes dans les règles de composition des mots,
        combine_dict_info = []
        for rule in rule_segment:
            rule_info = rule.strip('\n').split(',')
            if rule_info[0] == 'combine':
                if len(rule_info) == 4:
                    dict_info_combine = rule_info[2] + ',' + rule_info[3]

                    combine_dict_info.append(dict_info_combine)
        # Renvoyer le journal d'annotation, les mots et leurs étiquettes correspondantes.
        return annotate_text_info, combine_dict_info

    def annotate_tag(self, segment_info, dict_info):
        """
        Parcourir le dictionnaire, itérer à travers les mots du corpus, et mapper les étiquettes du dictionnaire dans le corpus.
        ex : taille,N,
        Si le mot 'taille' est présent dans la phrase, alors la clé aura l'étiquette 'N'
        Pour ce projet principal sur l'EPL, aucune annotation n'a été réalisée en utilisant un dictionnaire
        """
        for segment_dict_info in segment_info[1]:
            seg_dict_info = segment_dict_info.split(',')
            dict_info[seg_dict_info[0]] = seg_dict_info[1]
        for phrase in segment_info[0]:
            tag_table = {}
            phrase_info = []
            for index, word in enumerate(phrase['seg_phrase']):
                # Créer un dictionnaire pour enregistrer word, lemma, key,temp_info de chaque mot.
                tag_info = {}
                if word in list(dict_info):
                    tag_info['word'] = phrase['seg_phrase_original'][index]
                    tag_info['lemma'] = word
                    tag_info['key'] = dict_info[word]
                    tag_info['temp_info'] = ''
                    phrase_info.append(tag_info)

                else:
                    tag_info['word'] = phrase['seg_phrase_original'][index]
                    tag_info['lemma'] = word
                    tag_info['key'] = ''
                    tag_info['temp_info'] = ''
                    phrase_info.append(tag_info)
            tag_table['phrase'] = ' '.join(phrase['seg_phrase'])
            tag_table['table'] = phrase_info
            tag_table['seg_phrase_info'] = phrase
            # Appeler la méthode analyse_syntax()
            self.analyse_syntax(tag_table)

    # Enregistrer les résultats d'analyse au format JSON
    def save_json_result(self):
        with open(dict_out_file, 'w+', encoding='utf-8') as f:
            json.dump(self.tag_table_total, f, ensure_ascii=False, indent=2)

    def analyse_syntax(self, phrase_tag):
        # Lire les règles syntaxiques rule_syntax.txt
        with open(syntax_file, encoding='utf-8') as f:
            rule_syntax = f.readlines()
        # Parcourir les règles par niveau
        list_rule = []
        for index, syntax in enumerate(rule_syntax):
            # Lire l'ordre des règles.
            if index == 0:
                hierarchy = syntax.strip('\n').split(',')
                for rule_name in hierarchy:
                    list_rule.append(rule_name)
        dict_rule = {}
        # Classer les règles selon l'ordre spécifié par la première ligne de rule_syntax
        for index, rule_name in enumerate(list_rule):
            list_rule_hierarchy = []
            for syntax in rule_syntax:
                syntax_ = syntax.split(',')
                if syntax_[0] == rule_name:
                    list_rule_hierarchy.append(syntax)
            dict_rule[list_rule[index]] = list_rule_hierarchy

        dict_value = dict_rule.values()
        # Parcourir les règles catégorie par catégorie
        for hierarchy_rule in dict_value:
            # Parcourir les phrases avec des informations annotées
            for word_index, word_tag in enumerate(phrase_tag['table']):
                for rule in hierarchy_rule:
                    try:
                        if rule != '/':
                            syntax_info = rule.strip('\n').split(',')
                            # Si la règle est une expression régulière (reg),
                            # faire correspondre le modèle (pattern) avec l'expression (expr) dans la phrase,
                            # puis assigner l'étiquette (tag) de la règle aux mots correspondants.
                            # Ce projet n'implique pas ce morceau de code.
                            if syntax_info[1] == 'reg':
                                pattern = re.compile(syntax_info[2])
                                if pattern.fullmatch(word_tag['word']):
                                    tags_info = syntax_info[3].split(';')
                                    for tags in tags_info:
                                        tags_info_ = tags.split('==')
                                        word_tag[tags_info_[0]] = tags_info_[1]
                                    phrase_tag["seg_phrase_info"]['rule_info'].append(
                                        {'expr': word_tag['word'], 'rule': rule})
                            # Si la règle est de type syntaxe, parcourir la phrase et appliquer la règle.
                            if syntax_info[1] == 'syntax':

                                words_tag_index = syntax_info[2].split(';')
                                dict_tag_info = {}
                                # Extraire les informations de position de la syntaxe de rule_syntax,
                                # les informations de colonne key, les valeurs de colonne key, les informations de
                                # colonne temp_info et les valeurs de colonne temp_info, puis les convertir en listes
                                for word_tag_index in words_tag_index:
                                    # Convertir les informations de position, la clé et la valeur de la clé
                                    # de la règle syntaxique en dictionnaire
                                    tag_info_in_syntax = {}
                                    tag = word_tag_index[2:].strip().strip('[').strip(']').split('==')[0]
                                    tag_value = word_tag_index[2:].strip('[').strip(']').split('==')[1]
                                    tag_index_in_phrase = int(
                                        word_tag_index[:2].replace('L', '-').replace('R', '+').replace('CN', '0'))
                                    tag_info_in_syntax[tag] = tag_value
                                    dict_tag_info[tag_index_in_phrase] = tag_info_in_syntax
                                list_match_tag = []
                                list_value = []
                                for key, value in dict_tag_info.items():
                                    list_value.append(value)
                                    # Si les informations annotées dans CN de rule_syntax correspondent
                                    # aux informations annotées dans la phrase.

                                    if key == 0:
                                        for tag_key, tag_value in value.items():
                                            if word_tag[tag_key] == tag_value:
                                                # Parcourir à nouveau les index de la phrase localisée dans les règles.
                                                for key_again, value_again in dict_tag_info.items():
                                                    # Les index des mots à faire correspondre dans la phrase
                                                    # localisée par la règle."
                                                    word_index_in_phrase = word_index + key_again
                                                    if 0 <= word_index_in_phrase < len(phrase_tag['table']):

                                                        if phrase_tag['table'][word_index_in_phrase][
                                                            list(value_again)[0]] == \
                                                                value_again[list(value_again)[0]]:
                                                            list_match_tag.append(value_again)
                                # Si les informations de la règle correspondent aux annotations dans la phrase
                                if list_match_tag == list_value:
                                    # Si la règle contient 'combine', une opération de combinaison sera effectuée.
                                    if syntax_info[3][:syntax_info[3].index('[')] == 'combine':
                                        combine_index = syntax_info[3][syntax_info[3].index('['):].strip('[').strip(
                                            ']').split(
                                            '+')
                                        list_combine_index = []
                                        for index_in_combine in combine_index:
                                            index_num = int(
                                                index_in_combine.replace('CN', '0').replace('L', '-').replace('R',
                                                                                                              '+'))
                                            list_combine_index.append(index_num)
                                        range_list_combine_index = sorted(list_combine_index)
                                        index_start = range_list_combine_index[0] + word_index
                                        index_end = range_list_combine_index[1] + word_index
                                        list_expr = []
                                        list_lemme = []
                                        # Si les mots nécessitant une combinaison contiennent des tirets - ou des
                                        # apostrophes ' pour des abréviations,ils ne seront pas séparés par des
                                        # espaces. Ce code gère cette situation particulière
                                        trait = False
                                        for num in range(index_start, index_end + 1):
                                            if phrase_tag['table'][num]['word'][-1] in ['\'', '-']:
                                                trait = True
                                            list_expr.append(phrase_tag['table'][num]['word'])
                                            list_lemme.append(phrase_tag['table'][num]['lemma'])
                                        if trait:
                                            lemme_insert = ''
                                            expr_insert = ''
                                            for i, expr in enumerate(list_expr):
                                                if expr[-1] in ['-']:
                                                    lemme_insert = lemme_insert.rstrip()
                                                    expr_insert = expr_insert.rstrip()
                                                    expr_insert += expr
                                                    lemme_insert += list_lemme[i]
                                                elif expr[-1] in ['\'']:
                                                    expr_insert += expr
                                                    lemme_insert += list_lemme[i] + ' '
                                                else:
                                                    expr_insert += expr + ' '
                                                    lemme_insert += list_lemme[i] + ' '
                                            expr_insert = expr_insert.rstrip()
                                            lemme_insert = lemme_insert.rstrip()
                                        else:
                                            expr_insert = ' '.join(list_expr)
                                            lemme_insert = ' '.join(list_lemme)
                                        # Supprimer les mots d'origine dans la phrase et mettre
                                        # à jour les mots combinés.
                                        del phrase_tag['seg_phrase_info']['seg_phrase'][index_start:index_end + 1]
                                        phrase_tag['seg_phrase_info']['seg_phrase'].insert(index_start, expr_insert)
                                        del phrase_tag['seg_phrase_info']['seg_phrase_original'][
                                            index_start:index_end + 1]
                                        phrase_tag['seg_phrase_info']['seg_phrase_original'].insert(index_start,
                                                                                                    expr_insert)

                                        new_tag = syntax_info[4][syntax_info[4].index('['):].strip('[').strip(
                                            ']').split(
                                            '==')

                                        del phrase_tag['table'][index_start:index_end]
                                        new_word_tag = phrase_tag['table'][index_start]
                                        new_word_tag['word'] = expr_insert
                                        new_word_tag['lemma'] = lemme_insert
                                        new_word_tag[new_tag[0]] = new_tag[1]
                                        # Enregistrer la règle exécutée pour ce token
                                        phrase_tag["seg_phrase_info"]['rule_info'].append(
                                            {'expr': expr_insert, 'rule': rule})

                                    # Si la longueur avant le caractère '[' est de 2,
                                    # pouvant représenter CN, L1, R1, etc.,
                                    # il est considéré comme une règle syntax_tag.
                                    # Met à jour les résultats d'annotation dans le résultat de parser
                                    if len(syntax_info[3][:syntax_info[3].index('[')]) == 2:
                                        syntax_tag_info = syntax_info[3].split(';')
                                        dict_syntax_tag_info_total = {}
                                        for word_tag_info in syntax_tag_info:
                                            dict_syntax_tag_info = {}
                                            index_value = int(
                                                word_tag_info[:word_tag_info.index('[')].replace('CN', '0') \
                                                    .replace('L', '-').replace('R', '+'))

                                            tag = word_tag_info[word_tag_info.index('['):].strip(). \
                                                strip('[').strip(']').split('==')[0]
                                            tag_value = word_tag_info[word_tag_info.index('['):].strip(). \
                                                strip('[').strip(']').split('==')[1]
                                            dict_syntax_tag_info[tag] = tag_value
                                            dict_syntax_tag_info_total[index_value] = dict_syntax_tag_info
                                        for index_value, tag_info in dict_syntax_tag_info_total.items():
                                            locate_word_index = index_value + word_index
                                            for key, value in tag_info.items():
                                                phrase_tag['table'][locate_word_index][key] = value
                                        # Enregistrer la règle exécutée pour ce token
                                        phrase_tag["seg_phrase_info"]['rule_info'].append(
                                            {'expr': word_tag['word'], 'rule': rule})
                    except:
                        print('erreur de phrase:', phrase_tag['phrase'])
                        print('erreur de rule_syntax:', rule)
        self.tag_table_total.append(phrase_tag)

    # Ce code présente en format texte chaque phrase,
    # les résultats d'annotation de chaque mot et le code correspondant exécuté.
    # Cela permet d'analyser ces résultats pour mettre à jour les règles.
    def parser_result(self):
        with open(tag_text, 'w+', newline="", encoding='utf-8-sig') as f:
            for index, phrase_info in enumerate(self.tag_table_total):
                for index_, expr_info in enumerate(phrase_info['table']):
                    if index_ == 0:
                        line = '-' * 80 + '\n' + phrase_info['seg_phrase_info']['phrase_original'] + '\n' + '\n'
                        for rule in phrase_info['seg_phrase_info']['rule_info']:
                            line += rule['expr'] + '\n' + rule['rule'].rstrip('\n') + '\n'
                        line += '*' * 80 + '\n' + 'expr' + ' ' * (20 - len('expr')) + 'lemma' + ' ' * (
                                20 - len('lemma')) + 'Key' + ' ' * (20 - len('Key')) + 'temp_info' + '\n' + \
                                expr_info['word'] + ' ' * (20 - len(expr_info['word'])) + expr_info['lemma'] + ' ' * (
                                        20 - len(expr_info['lemma'])) + expr_info['key'] + ' ' * (
                                        20 - len(expr_info['key'])) + expr_info['temp_info'] + '\n'
                    else:
                        line += expr_info['word'] + ' ' * (20 - len(expr_info['word'])) + expr_info['lemma'] \
                                + ' ' * (20 - len(expr_info['lemma'])) + expr_info['key'] + ' ' * (
                                        20 - len(expr_info['key'])) + expr_info[
                                    'temp_info'] + '\n'

                f.write(line)

        with open(dict_out_file, 'w+', newline="", encoding='utf-8') as f:
            json.dump(self.tag_table_total, f, ensure_ascii=False, indent=2)

    # lire le fichier EPL_info.txt.
    def add_dict_info_text(self):
        with open(EPL_info_file, encoding='utf-8', mode='r') as f:
            json_data = f.readlines()
        EPL_info = []
        for data in json_data:
            word_dict = eval(data)
            EPL_info.append(word_dict)
        # Parcourir les résultats d'annotation
        for phrase_info in self.tag_table_total:
            phrase_info['replace'] = False
            phrase_info['replace_phrase'] = ''
            for word_info in phrase_info['table']:
                word_info['EPL_info'] = ''
                word_info['replace'] = 'None'
                word_info['exercise'] = ' '
                # Si la clé de ce mot est EPL
                if word_info['key'] == 'EPL':
                    # Parcourir le fichier EPL_info.
                    for EPL_word_info in EPL_info:
                        # Si le mot des résultats d'annotation correspond au mot dans EPL_info.
                        if EPL_word_info['EPL'] == word_info['lemma']:
                            # Met à jour les informations de EPL_info dans les résultats d'analyse correspondants
                            word_info['EPL_info'] = EPL_word_info['table']
                            word_info['exercise'] = EPL_word_info['exercise']
                            word_info['replace'] = EPL_word_info['replace']
                            if EPL_word_info['replace'] != 'None':
                                phrase_info['replace'] = True
            if phrase_info['replace']:
                list_word = []
                for word_info in phrase_info['table']:
                    if word_info['replace'] == 'None':
                        list_word.append(word_info['word'])
                    else:
                        list_word.append(word_info['replace'])
                expr_replace = ' '.join(list_word)
                phrase_info['replace_phrase'] = expr_replace


if __name__ == '__main__':
    annotate_french = annotate_text()
    french_text = annotate_french.read_text(input_file)
    dict_epl = annotate_french.read_dict()
    # Parcourir le texte ligne par ligne."
    for line in french_text:
        # Diviser les phrases avec '\n'
        lines = line.split('\\n')
        for line in lines:
            phrase_correct = ''
            list_tag_info = [[], []]
            # Utiliser la lemmatisation pour effectuer la lemmatisation et la tokenisation.
            text_line = annotate_french.lemmatisation(line)
            for phrase, tag in text_line.items():
                phrase_correct += phrase
                list_tag_info[0] += tag[0]
                list_tag_info[1] += tag[1]
            # Appeler cut_sentence pour identifier l'EPL
            list_seg_info = annotate_french.cut_sentence(phrase_correct, list_tag_info)
            # Appeler annotate_tag pour mettre à jours l'annotation
            annotate_french.annotate_tag(list_seg_info, dict_epl)
    # Afficher les résultats d'annotation.
    annotate_french.parser_result()
    # Met à jour les informations du fichier EPL_info.txt dans les résultats d'annotation
    annotate_french.add_dict_info_text()
    # Sauvegarder le fichier au format JSON
    annotate_french.save_json_result()
