from dataclasses import dataclass

from ..llm import LLMError, OllamaClient
from .crawler import Candidate

MAX_CANDIDATES = 10

SYSTEM = """Tu aides des utilisateurs à supprimer leurs comptes en ligne.
Tu reçois une liste numérotée de liens trouvés sur un site.
Choisis le lien qui mène LE PLUS DIRECTEMENT à la suppression ou la fermeture du compte :
1. page ou formulaire de suppression du compte
2. page des paramètres du compte qui contient la suppression
3. article d'aide qui explique comment supprimer le compte
4. page pour exercer ses droits RGPD (effacement des données)
Ne choisis jamais une page de connexion, d'inscription, de blog, de cookies ou de marketing.
Chaque lien peut avoir un extrait de la page : base-toi d'abord sur l'extrait, puis sur l'URL.
Une page de compte ou de profil qui redirige vers la connexion reste un bon choix si son URL
indique clairement les paramètres du compte : la suppression s'y fait une fois connecté.
Réponds avec index = -1 si aucun lien ne concerne la suppression du compte ou les droits RGPD.
La raison doit être courte et en français."""

SCHEMA = {
    "type": "object",
    "properties": {
        "index": {"type": "integer"},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["index", "confidence", "reason"],
}


@dataclass
class Choice:
    candidate: Candidate
    confidence: float
    reason: str


def build_prompt(domain: str, candidates: list[Candidate], service: str | None = None) -> str:
    lines = [f"Site : {service or domain} ({domain})", "Liens :"]
    for i, c in enumerate(candidates):
        line = f"{i}. {c.url} | texte du lien : {c.text or '-'}"
        if c.excerpt:
            line += f"\n   page -> {c.excerpt}"
        lines.append(line)
    return "\n".join(lines)


async def rank(llm: OllamaClient, domain: str, candidates: list[Candidate],
               service: str | None = None) -> Choice | None:
    cands = candidates[:MAX_CANDIDATES]
    if not cands:
        return None
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": build_prompt(domain, cands, service)}]
    try:
        ans = await llm.chat_json(messages, SCHEMA)
        index = int(ans["index"])
        confidence = min(max(float(ans["confidence"]), 0.0), 1.0)
        reason = str(ans["reason"])[:300]
    except (LLMError, KeyError, TypeError, ValueError):
        return None
    if not 0 <= index < len(cands):
        return None
    return Choice(cands[index], confidence, reason)
