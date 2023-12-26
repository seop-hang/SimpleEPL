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
tag_out_file = './annotated_text.csv'
tag_text = './parser_result.txt'
EPL_info_file = './EPL_info.txt'


class annotate_text:
    def __init__(self):
        self.tag_table_total = []

    def read_text(self, file):
        with open(file, encoding='utf-8') as f:
            phrases = f.readlines()
            return phrases

    def read_dict(self):
        """
        读取dic_radio字典，转换成结巴需要的格式，并保存
        :return:
        """
        with open(dict_file, 'r', encoding='utf-8') as f:
            tags_info = f.readlines()
            dict_tag_info = {}
            # 将dic_radio文件转换成字典
            list_dict_info = []
            for word_tag_info in tags_info:
                try:
                    dict_info = word_tag_info.strip('\n').split(',')
                    dict_tag_info[dict_info[0]] = dict_info[1]
                    list_dict_info.append(dict_info[0])
                except:
                    print('Erreur de lecture du dictionnaire:', word_tag_info)
                # 保存为结巴分词格式的字典
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

        doc = nlp(text)
        sents_dict = {}
        for sent in doc.sents:
            if sent not in sents_dict:
                tokens_formes = [[], []]
                for i, token in enumerate(sent):
                    tokens_formes[1].append(token.text)
                    tokens_formes[0].append(token.lemma_)
                    sents_dict[sent.text] = tokens_formes

        return sents_dict

    def cut_sentence(self, sentence, sentence_seg):
        """
        通过词典，分词、合词规则进行精确分词

        :param self:
        :return:
        """

        annotate_text_info = []
        # 读取分词规则
        items = {"rule_info": []}
        with open(segment_file, encoding='utf-8') as f:
            rule_segment = f.readlines()

        words = sentence_seg[0]
        list_words = []
        # 读取分词规则，进行分词
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

        # 读取合词规则，进行合词
        for index_word, word in enumerate(list_words):
            for rule in rule_segment:
                if rule[0] != '/':
                    rule_info = rule.strip('\n').split(',')
                    if rule_info[0] == 'combine':

                        combine_info = rule_info[1].split('+')
                        if word == combine_info[0]:

                            find_combine_value = []
                            find_combine_index = []
                            for index_seg, seg_info in enumerate(combine_info):

                                if index_word + index_seg < len(list_words):
                                    if seg_info == list_words[index_word + index_seg]:
                                        find_combine_value.append(seg_info)
                                        find_combine_index.append(index_word + index_seg)
                            expr = ' '.join(find_combine_value)
                            if expr == rule_info[2]:

                                expr_orig = ' '.join(
                                    sentence_seg[1][find_combine_index[0]:find_combine_index[-1] + 1])
                                for index_combine in find_combine_index:
                                    del list_words[find_combine_index[0]]
                                    del sentence_seg[1][find_combine_index[0]]
                                list_words.insert(find_combine_index[0], expr)
                                sentence_seg[1].insert(find_combine_index[0], expr_orig)

                                # sentence_seg[1].insert(find_combine_index[0], expr_orig)
                                items['rule_info'].append({'expr': expr, 'rule': rule})
        items['seg_phrase'] = list_words
        items['seg_phrase_original'] = sentence_seg[1]
        items['phrase_original'] = sentence
        annotate_text_info.append(items)
        # 将合词规则中的词和对应标签列表存储，传入annotate_tag
        combine_dict_info = []
        for rule in rule_segment:
            rule_info = rule.strip('\n').split(',')
            if rule_info[0] == 'combine':
                if len(rule_info) == 4:
                    dict_info_combine = rule_info[2] + ',' + rule_info[3]

                    combine_dict_info.append(dict_info_combine)
        return annotate_text_info, combine_dict_info

    def annotate_tag(self, segment_info, dict_info):
        """
        读取字典，遍历语料的词，将字典的标签映射到语料中
        """
        # tag_table_phrase = []
        for segment_dict_info in segment_info[1]:
            seg_dict_info = segment_dict_info.split(',')
            dict_info[seg_dict_info[0]] = seg_dict_info[1]
        for phrase in segment_info[0]:
            tag_table = {}
            phrase_info = []
            for index, word in enumerate(phrase['seg_phrase']):
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

            self.analyse_syntax(tag_table)

    def save_json_result(self):
        with open(dict_out_file, 'w+', encoding='utf-8') as f:
            json.dump(self.tag_table_total, f, ensure_ascii=False, indent=2)

    def analyse_syntax(self, phrase_tag):
        # 读取句法规则
        with open(syntax_file, encoding='utf-8') as f:
            rule_syntax = f.readlines()
        # 按层级读规则
        list_rule = []
        for index, syntax in enumerate(rule_syntax):
            # 读取规则顺序
            if index == 0:
                hierarchy = syntax.strip('\n').split(',')
                for rule_name in hierarchy:
                    list_rule.append(rule_name)
        dict_rule = {}
        # 将规则按rule_syntax第一行的排序进行分类
        for index, rule_name in enumerate(list_rule):
            list_rule_hierarchy = []
            for syntax in rule_syntax:
                syntax_ = syntax.split(',')
                if syntax_[0] == rule_name:
                    list_rule_hierarchy.append(syntax)
            dict_rule[list_rule[index]] = list_rule_hierarchy

        dict_value = dict_rule.values()
        # 逐类遍历规则
        for hierarchy_rule in dict_value:
            # 遍历带标注信息句子
            for word_index, word_tag in enumerate(phrase_tag['table']):
                # print(word_tag)
                for rule in hierarchy_rule:
                    try:
                        if rule != '/':
                            syntax_info = rule.strip('\n').split(',')
                            # 如果规则为reg(正则表达式),将pattern和句子中的expr进行匹配，映射规则中的tag到匹配上的词上
                            if syntax_info[1] == 'reg':
                                pattern = re.compile(syntax_info[2])
                                if pattern.fullmatch(word_tag['word']):
                                    tags_info = syntax_info[3].split(';')
                                    for tags in tags_info:
                                        tags_info_ = tags.split('==')
                                        word_tag[tags_info_[0]] = tags_info_[1]
                                    phrase_tag["seg_phrase_info"]['rule_info'].append(
                                        {'expr': word_tag['word'], 'rule': rule})
                            # 如果规则为syntax类型，遍历句子，匹配规则
                            if syntax_info[1] == 'syntax':

                                words_tag_index = syntax_info[2].split(';')
                                dict_tag_info = {}
                                # 提取rule_syntax中的syntax中的位置信息,key列信息、key值,temp_info列信息,temp_info值,并转换成列表
                                for word_tag_index in words_tag_index:
                                    # 将syntax规则中的位置信息,key,key_value转换成dict
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
                                    # 如果rule_syntax中CN中标注信息和句子标注信息匹配
                                    if key == 0:
                                        for tag_key, tag_value in value.items():
                                            if word_tag[tag_key] == tag_value:
                                                # 再次遍历规则中定位的句子中的索引
                                                for key_again, value_again in dict_tag_info.items():
                                                    # 规则定位的句子中需匹配的词的索引
                                                    word_index_in_phrase = word_index + key_again
                                                    if 0 <= word_index_in_phrase < len(phrase_tag['table']):

                                                        if phrase_tag['table'][word_index_in_phrase][
                                                            list(value_again)[0]] == \
                                                                value_again[list(value_again)[0]]:
                                                            list_match_tag.append(value_again)

                                if list_match_tag == list_value:
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

                                        del phrase_tag['seg_phrase_info']['seg_phrase'][index_start:index_end + 1]
                                        phrase_tag['seg_phrase_info']['seg_phrase'].insert(index_start, expr_insert)
                                        del phrase_tag['seg_phrase_info']['seg_phrase_original'][
                                            index_start:index_end + 1]
                                        phrase_tag['seg_phrase_info']['seg_phrase_original'].insert(index_start,
                                                                                                    expr_insert)
                                        # del phrase_tag['table'][index_start:index_end + 1]
                                        new_tag = syntax_info[4][syntax_info[4].index('['):].strip('[').strip(
                                            ']').split(
                                            '==')
                                        # print(index_start, phrase_tag['table'][index_start], index_end + 1,
                                        #       phrase_tag['table'][index_end])

                                        del phrase_tag['table'][index_start:index_end]
                                        new_word_tag = phrase_tag['table'][index_start]
                                        new_word_tag['word'] = expr_insert
                                        new_word_tag['lemma'] = lemme_insert
                                        new_word_tag[new_tag[0]] = new_tag[1]

                                        # phrase_tag['table'].insert(index_start, new_word_tag)
                                        # 判断如果'['字符前面长度为2，可能为CN,L1,R1等，判定为syntax_tag规则
                                        phrase_tag["seg_phrase_info"]['rule_info'].append(
                                            {'expr': expr_insert, 'rule': rule})
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
                                        phrase_tag["seg_phrase_info"]['rule_info'].append(
                                            {'expr': word_tag['word'], 'rule': rule})
                    except:
                        print('erreur de phrase:', phrase_tag['phrase'])
                        print('erreur de rule_syntax:', rule)
        self.tag_table_total.append(phrase_tag)

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

    def add_dict_info_text(self):
        with open(EPL_info_file, encoding='utf-8', mode='r') as f:
            json_data = f.readlines()
        EPL_info = []
        for data in json_data:
            word_dict = eval(data)
            EPL_info.append(word_dict)
        for phrase_info in self.tag_table_total:
            phrase_info['replace'] = False
            phrase_info['replace_phrase'] = ''

            for word_info in phrase_info['table']:
                word_info['EPL_info'] = ''
                word_info['replace'] = 'None'
                word_info['exercise'] = ' '
                if word_info['key'] == 'EPL':
                    for EPL_word_info in EPL_info:
                        if EPL_word_info['EPL'] == word_info['lemma']:
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

    for line in french_text:

        lines = line.split('\\n')
        for line in lines:
            phrase_correct = ''
            list_tag_info = [[], []]
            text_line = annotate_french.lemmatisation(line)
            for phrase, tag in text_line.items():
                phrase_correct += phrase
                list_tag_info[0] += tag[0]
                list_tag_info[1] += tag[1]

            list_seg_info = annotate_french.cut_sentence(phrase_correct, list_tag_info)
            annotate_french.annotate_tag(list_seg_info, dict_epl)
    annotate_french.save_json_result()
    annotate_french.parser_result()
    annotate_french.add_dict_info_text()
    annotate_french.save_json_result()