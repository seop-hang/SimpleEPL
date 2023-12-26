async function switchContent(contentId) {
    // la fonction pour changer le niveau
    // quand on clique sur un élément "li", on reconnaît le niveau correspondant et change la couleur de cet élément
    let lis = document.querySelectorAll(".menu li");
    for (let i = 0; i < lis.length; i++) {
        if (i + 1 === contentId) {
            lis[i].classList.add("colored");
        } else {
            lis[i].classList.remove("colored");
        }
    }
    // on reconnaît le niveau, et envoie une requête avec un nom du fichier correspondant
    let colis={}
    switch (contentId) {
        case 1:
            colis.filename='a1.json'
            break
        case 2:
            colis.filename='a2.json'
            break
        case 3:
            colis.filename='b1.json'
            break
        case 4:
            colis.filename='b2.json'
            break
        case 5:
            colis.filename='c1.json'
            break
        case 6:
            colis.filename='c2.json'
            break
    }
    const requete={
        method:'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(colis)
    }
    const response=await fetch('/home/',requete);
    const data=await response.json();
    // avec la réponse, on change le contenu
    document.getElementById("content1").innerHTML = data.reponse;
    document.getElementById("content2").innerHTML = data.reponse2;
    document.getElementById("explainContainer").innerHTML = data.reponse3;
}

function switchToExercice() {
    // la fonction pour changer à la page d'exercices
    // quand on clique sur le boutton "Go to exercises", on reconnaît le niveau actuel et change la page en adjoignant
    // ce niveau
    let lis = document.querySelectorAll(".menu li");
    let index=0
    let filename=""
    for (let i = 0; i < lis.length; i++) {
        if (lis[i].classList.contains("colored")) {
            index=i;
        }
    }
    switch (index+1) {
        case 1:
            filename='a1.json'
            break
        case 2:
            filename='a2.json'
            break
        case 3:
            filename='b1.json'
            break
        case 4:
            filename='b2.json'
            break
        case 5:
            filename='c1.json'
            break
        case 6:
            filename='c2.json'
            break
    }
    // Redirect to the "exercices" page
    window.location.href = "/exercices"+`?filename=${filename}`;
}