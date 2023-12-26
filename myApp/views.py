from django.shortcuts import render
from django.http import JsonResponse
import json,spacy
import os
import random
import Levenshtein
from django.conf import settings
media_root = settings.MEDIA_ROOT
nlp = spacy.load("fr_core_news_md")

# Create your views here.

# la page d'accueil
def home(request):
    # par défault, quand on entre dans la plateforme, on voit le contenu du niveau A1
    # on ouvre le fichier json du niveau A1, et lire le contenu
    dict_out_file = os.path.join(media_root, 'a1.json')
    with open(dict_out_file,'r',encoding='utf-8') as file:
        data=json.load(file)
    text=""
    replaced_text=""
    explication=""
    explication_num=1
    # on parcourt toutes les phrases, on sauvegrade les phrases originales et les phrases remplacées, et on parcourt tous
    # les tokens, si il s'agit d'une expression polylexicale, on le rend en couleur rouge, et on sauvegarde les explications
    # correspondantes
    for phrase in data:
        original_phrase=phrase['seg_phrase_info']['phrase_original']
        replaced_phrase=phrase['seg_phrase_info']['phrase_original']
        tokens=phrase["table"]
        for token in tokens:
            if token['key']=='EPL':
                original_phrase=original_phrase.replace(token['word'],"<span style='color: red;'>"+token['word']+"</span>")
                explication+="<p style='text-align: justify;'>"+str(explication_num)+". "+token['word']+" :&emsp;&emsp;"
                for k,v in token['EPL_info'][0].items():
                    explication=explication+"<span>"+k+" : "+v+"&emsp;&emsp;&emsp;</span>"
                explication_num+=1
                explication += "</p>"
                if token['replace'] != "None":
                    replaced_phrase=replaced_phrase.replace(token['word'],"<span style='color: blue;'>"+token['replace']+"</span>")
        text=text+"<p style='text-align: justify;'>"+original_phrase+"</p>"
        replaced_text=replaced_text+"<p style='text-align: justify;'>"+replaced_phrase+"</p>"
    return render(request, 'home.html',{'processed_data':text,'replaced_text':replaced_text,'explain':explication})

def exercices(request):
    # la fonction pour changer à la page d'exercice
    # on récupère le nom du fichier envoyé dans la requête, et parcourt tous les phrase, si on trouve un exercice, on
    # dérange l'ordre des tokens dans cet exercice, et envoie cette phrase dérangée et la phrase orignale
    filename=request.GET.get('filename')
    dict_out_file = os.path.join(media_root, filename)
    with open(dict_out_file,'r',encoding='utf-8') as file:
        data=json.load(file)
    references=[]
    exercices=[]
    for phrase in data:
        tokens=phrase['table']
        for token in tokens:
            if token['exercise'] != " ":
                exercice=token['exercise'].split(" ")
                references.append(token['exercise'].split(" "))
                random.shuffle(exercice)
                exercices.append(exercice)
    return render(request, 'exercices.html',{'exercices':exercices,'references':references})

def change(request):
    # la fonction pour le changement du niveau
    # on récupère le nom du fichier dans la requête, et traite ce fichier de la même façon que l'initialisation du page
    # web et ensuite envoie la réponse
    colis = json.loads(request.body)
    filename = colis['filename']
    dict_out_file = os.path.join(media_root, filename)
    with open(dict_out_file,'r',encoding='utf-8') as file:
        data=json.load(file)
    text=""
    replaced_text=""
    explication=""
    explication_num=1
    for phrase in data:
        original_phrase=phrase['seg_phrase_info']['phrase_original']
        replaced_phrase=phrase['seg_phrase_info']['phrase_original']
        tokens=phrase["table"]
        for token in tokens:
            if token['key']=='EPL':
                original_phrase=original_phrase.replace(token['word'],"<span style='color: red;'>"+token['word']+"</span>")
                explication+="<p style='text-align: justify;'>"+str(explication_num)+". "+token['word']+" :&emsp;&emsp;"
                for k,v in token['EPL_info'][0].items():
                    explication=explication+"<span>"+k+" : "+v+"&emsp;&emsp;&emsp;</span>"
                explication_num+=1
                explication += "</p>"
                if token['replace'] != "None":
                    replaced_phrase=replaced_phrase.replace(token['word'],"<span style='color: blue;'>"+token['replace']+"</span>")
        text=text+"<p style='text-align: justify;'>"+original_phrase+"</p>"
        replaced_text=replaced_text+"<p style='text-align: justify;'>"+replaced_phrase+"</p>"

    reponse={
        'reponse':text,
        'reponse2':replaced_text,
        'reponse3':explication
    }
    return JsonResponse(reponse)