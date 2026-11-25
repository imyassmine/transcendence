from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class LegalRef:
    ref: str
    summary: str


class Ground(StrEnum):

    NO_LONGER_NEEDED = "no_longer_needed"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    OBJECTION = "objection"
    UNLAWFUL = "unlawful"


REFS: dict[str, LegalRef] = {
    "17.1": LegalRef(
        "article 17, paragraphe 1, du RGPD",
        "Droit d'obtenir du responsable du traitement l'effacement de ses données dans les "
        "meilleurs délais, lorsqu'un des motifs du paragraphe s'applique."),
    "17.1.a": LegalRef(
        "article 17, paragraphe 1, point a)",
        "Motif : les données ne sont plus nécessaires au regard des finalités pour "
        "lesquelles elles ont été collectées (ex. compte inutilisé)."),
    "17.1.b": LegalRef(
        "article 17, paragraphe 1, point b)",
        "Motif : la personne retire le consentement sur lequel le traitement est fondé et "
        "il n'existe pas d'autre fondement juridique."),
    "7.3": LegalRef(
        "article 7, paragraphe 3",
        "Le consentement peut être retiré à tout moment, aussi simplement qu'il a été donné."),
    "17.1.c": LegalRef(
        "article 17, paragraphe 1, point c)",
        "Motif : la personne s'oppose au traitement en application de l'article 21."),
    "21.2": LegalRef(
        "article 21, paragraphes 2 et 3",
        "Droit absolu de s'opposer à tout moment au traitement à des fins de prospection, "
        "profilage compris ; les données ne sont alors plus traitées à ces fins."),
    "17.1.d": LegalRef(
        "article 17, paragraphe 1, point d)",
        "Motif : les données ont fait l'objet d'un traitement illicite."),
    "17.2": LegalRef(
        "article 17, paragraphe 2",
        "Si les données ont été rendues publiques, le responsable prend des mesures "
        "raisonnables pour informer les autres responsables de la demande d'effacement."),
    "17.3": LegalRef(
        "article 17, paragraphe 3",
        "Exceptions limitées (obligation légale de conservation, constatation ou défense de "
        "droits en justice, etc.) : le responsable doit alors pouvoir les justifier."),
    "19": LegalRef(
        "article 19",
        "Le responsable notifie l'effacement à chaque destinataire auquel les données ont "
        "été communiquées, sauf impossibilité ou effort disproportionné."),
    "12.3": LegalRef(
        "article 12, paragraphe 3",
        "Réponse dans un délai d'un mois à compter de la réception de la demande, "
        "prolongeable de deux mois si nécessaire, la personne étant informée de la "
        "prolongation et de ses motifs dans le premier mois."),
    "12.5": LegalRef(
        "article 12, paragraphe 5",
        "L'exercice des droits est gratuit."),
    "77": LegalRef(
        "article 77",
        "Droit d'introduire une réclamation auprès d'une autorité de contrôle "
        "(en France : la CNIL, www.cnil.fr)."),
}

GROUND_REFS: dict[Ground, list[str]] = {
    Ground.NO_LONGER_NEEDED: ["17.1.a"],
    Ground.CONSENT_WITHDRAWN: ["17.1.b", "7.3"],
    Ground.OBJECTION: ["17.1.c", "21.2"],
    Ground.UNLAWFUL: ["17.1.d"],
}

ALWAYS = ["17.1", "17.3", "19", "12.3", "12.5", "77"]


def select_refs(grounds: set[Ground], data_public: bool) -> list[str]:
    keys = ["17.1"]
    for g in Ground:
        if g in grounds:
            keys += GROUND_REFS[g]
    if data_public:
        keys.append("17.2")
    keys += [k for k in ALWAYS if k not in keys]
    return keys


def allowed_article_numbers(keys: list[str]) -> set[int]:
    return {int(k.split(".")[0]) for k in keys}
