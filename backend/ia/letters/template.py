import re
from datetime import date

from .gdpr import Ground
from .models import LetterRequest


def default_context(req: LetterRequest) -> str:
    if req.breached:
        return ("Ce compte figurant dans une fuite de données connue, je souhaite réduire au plus "
                "vite l'exposition de mes informations personnelles.")
    return ""


def render_header(req: LetterRequest) -> str:
    ident = f"l'adresse e-mail {req.account_email}"
    if req.username:
        ident += f" (identifiant : {req.username})"
    return f"Madame, Monsieur,\n\nJe suis titulaire d'un compte {req.service_name} associé à {ident}.\n\n"


def render_template(req: LetterRequest, grounds: set[Ground], context: str | None = None) -> str:
    return render_header(req) + _context_block(req, context) + render_legal(req, grounds)


def _context_block(req: LetterRequest, context: str | None) -> str:
    text = (context if context is not None else default_context(req)).strip()
    return f"{text}\n\n" if text else ""


def render_legal(req: LetterRequest, grounds: set[Ground]) -> str:
    motifs = []
    if Ground.NO_LONGER_NEEDED in grounds:
        since = f" depuis {req.inactive_since:%m/%Y}" if req.inactive_since else ""
        motifs.append("mes données ne sont plus nécessaires au regard des finalités pour "
                      f"lesquelles elles ont été collectées, ce compte n'étant plus utilisé{since} "
                      "(article 17, paragraphe 1, point a)")
    if Ground.CONSENT_WITHDRAWN in grounds:
        motifs.append("je retire mon consentement au traitement de mes données, comme "
                      "l'article 7, paragraphe 3, m'y autorise à tout moment (article 17, "
                      "paragraphe 1, point b)")
    if Ground.OBJECTION in grounds:
        motifs.append("je m'oppose au traitement de mes données, en particulier à toute "
                      "utilisation à des fins de prospection, y compris le profilage "
                      "(article 21, paragraphes 2 et 3, et article 17, paragraphe 1, point c)")
    if Ground.UNLAWFUL in grounds:
        motifs.append("mes données ont fait l'objet d'un traitement illicite "
                      "(article 17, paragraphe 1, point d)")
    motifs_txt = " ;\n".join(f"- {m}" for m in motifs) + "."

    extra = []
    if req.data_public:
        extra.append("Certaines de ces données ayant été rendues publiques, je vous demande "
                     "également d'informer les autres responsables de traitement concernés, "
                     "conformément à l'article 17, paragraphe 2.")

    text = f"""En application de l'article 17, paragraphe 1, du Règlement général sur la protection des données (RGPD), je vous demande de supprimer ce compte et d'effacer l'ensemble des données personnelles me concernant que vous détenez, pour les motifs suivants :
{motifs_txt}

{" ".join(extra)}

Conformément à l'article 19 du RGPD, je vous remercie de notifier cet effacement à chacun des destinataires auxquels ces données ont été communiquées. Si certaines données devaient être conservées au titre d'une exception prévue à l'article 17, paragraphe 3, merci de m'indiquer précisément lesquelles, le fondement juridique invoqué et la durée de conservation.

Conformément à l'article 12, paragraphe 3, vous disposez d'un délai d'un mois à compter de la réception de cette demande pour y répondre ; l'exercice de ce droit est gratuit (article 12, paragraphe 5). Je vous saurais gré de me confirmer par écrit la suppression effective de mon compte et de mes données.

À défaut de réponse satisfaisante dans ce délai, je me réserve la possibilité d'introduire une réclamation auprès de la CNIL, conformément à l'article 77 du RGPD.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

{req.full_name}
Le {date.today():%d/%m/%Y}
"""
    return re.sub(r"\n{3,}", "\n\n", text)
