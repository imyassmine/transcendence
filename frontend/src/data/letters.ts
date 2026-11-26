import type { Organisation } from './organisations'

export type Letter = {
  subject: string
  body: string
  recipient_email: string | null
  contact_url: string | null
  legal_refs: string[]
  generated_by: 'llm' | 'template'
  warnings: string[]
}

export type Ground =
  | 'no_longer_needed'
  | 'consent_withdrawn'
  | 'objection_legitimate_interest'
  | 'objection_marketing'
  | 'unlawful'
  | 'minor_at_signup'

export type LetterRequest = {
  request_id: string
  full_name: string
  account_email: string
  service_name: string
  username: string | null
  has_account: boolean
  recipient_email: string | null
  contact_url: string | null
  grounds: Ground[]
  inactive_since: string | null
  data_public: boolean
  is_broker: boolean
  breached: boolean
  context: string | null
}

export type LetterLanguage = 'en' | 'fr' | 'es'

export const LETTER_LANGUAGES: LetterLanguage[] = ['en', 'fr', 'es']

const GROUND_ORDER: Ground[] = [
  'no_longer_needed',
  'consent_withdrawn',
  'objection_legitimate_interest',
  'objection_marketing',
  'unlawful',
  'minor_at_signup',
]

const GROUND_REFS: Record<Ground, string[]> = {
  no_longer_needed: ['17(1)(a)', '5(1)(e)'],
  consent_withdrawn: ['17(1)(b)', '7(3)'],
  objection_legitimate_interest: ['21(1)', '17(1)(c)', '18(1)(d)'],
  objection_marketing: ['21(2)', '21(3)', '17(1)(c)'],
  unlawful: ['17(1)(d)'],
  minor_at_signup: ['17(1)(f)', '8(1)'],
}

type Texts = {
  abbr: string
  recipient: string
  date: (formatted: string) => string
  subjectLabel: string
  refLabel: string
  subject: (service: string, hasAccount: boolean) => string
  greeting: string
  identity: (service: string, email: string, username: string | null) => string
  identityNoAccount: (service: string, email: string) => string
  listSeparator: string
  breachContext: string
  titles: [string, string, string, string, string]
  request: (closeAccount: boolean) => string
  groundsIntro: string
  grounds: Record<Ground, (inactiveSince: string | null) => string>
  restriction: string
  recipients: string
  dataPublic: string
  source: string
  breach: string
  exceptions: string
  deadline: string
  confirm: string
  remedies: string
  closing: string
}

const TEXTS: Record<LetterLanguage, Texts> = {
  en: {
    abbr: 'GDPR',
    recipient: 'Data Protection Officer (DPO)',
    date: (formatted) => formatted,
    subjectLabel: 'Subject:',
    refLabel: 'Ref.:',
    subject: (service, hasAccount) => `Request for erasure of personal data – Article 17 GDPR – ${service}${hasAccount ? ' account' : ''}`,
    greeting: 'Dear Sir or Madam,',
    identity: (service, email, username) =>
      `I hold an account with ${service} associated with the email address ${email}${username ? ` (username: ${username})` : ''}. `
      + 'This information is sufficient to identify me. Under Article 12(6) GDPR, additional information may only be requested '
      + 'where you have reasonable doubts concerning my identity, and only to the extent necessary to confirm it.',
    identityNoAccount: (service, email) =>
      `I have reason to believe that ${service} processes personal data concerning me, in particular data linked to the email address ${email}. `
      + 'This information is sufficient to identify me. Under Article 12(6) GDPR, additional information may only be requested '
      + 'where you have reasonable doubts concerning my identity, and only to the extent necessary to confirm it.',
    listSeparator: ';',
    breachContext:
      'As this account appears in a known data breach, I wish to reduce the exposure of my personal information as quickly as possible.',
    titles: ['1. Request', '2. Grounds', '3. Additional measures requested', '4. Time limit', '5. Remedies'],
    request: (closeAccount) =>
      'Pursuant to Article 17(1) of Regulation (EU) 2016/679 of 27 April 2016 (General Data Protection Regulation, "GDPR"), '
      + 'I request that you erase without undue delay all personal data concerning me that you process, including derived data, '
      + `profiles, marketing segments and backup copies${closeAccount ? ', and that you close the above-mentioned account' : ''}.`,
    groundsIntro: 'This request is based on the following grounds:',
    grounds: {
      no_longer_needed: (since) =>
        'the data are no longer necessary in relation to the purposes for which they were collected, '
        + `as the account ${since ? `has not been used since ${since}` : 'is no longer used'} (Article 17(1)(a)), `
        + 'in accordance with the storage limitation principle (Article 5(1)(e))',
      consent_withdrawn: () =>
        'I withdraw, with immediate effect, any consent I may have given to the processing of my data (Article 7(3)), '
        + 'and there is no other legal ground for the processing (Article 17(1)(b))',
      objection_legitimate_interest: () =>
        'I object, on grounds relating to my particular situation, to the processing of my data based on your legitimate interests '
        + '(Article 21(1)). It is for you to demonstrate compelling legitimate grounds which override my interests, rights and freedoms; '
        + 'failing that, the data must be erased (Article 17(1)(c))',
      objection_marketing: () =>
        'I object to any processing of my data for direct marketing purposes, including profiling related to such marketing '
        + '(Article 21(2) and (3)). This right is absolute and requires no justification',
      unlawful: () => 'my data have been unlawfully processed (Article 17(1)(d))',
      minor_at_signup: () =>
        'my data were collected in relation to the offer of information society services while I was a minor '
        + '(Article 17(1)(f) and Article 8(1))',
    },
    restriction:
      'Pending verification of whether your legitimate grounds override mine, I request that you restrict the processing of my data '
      + '(Article 18(1)(d)).',
    recipients:
      'Under Article 19, please communicate this erasure to each recipient to whom my data have been disclosed, and inform me about those recipients.',
    dataPublic:
      'If you have made these data public, please take reasonable steps to inform the controllers processing them that I have requested '
      + 'the erasure of any links to, or copies or replications of, these data (Article 17(2)).',
    source: 'As my data were not obtained from me, please tell me their source (Article 14(2)(f) and Article 15(1)(g)).',
    breach:
      'As this account appears in a data breach, please tell me whether my data were affected and which categories of data were concerned. '
      + 'Where a breach is likely to result in a high risk to my rights and freedoms, you are required to inform me (Article 34).',
    exceptions:
      'If you consider that some data must be retained under one of the exceptions in Article 17(3), please specify which data, '
      + 'the legal basis relied on and the retention period. All other data must be erased without delay.',
    deadline:
      'Under Article 12(3), you must act on this request within one month of receipt. This period may be extended by two further months '
      + 'only where necessary, taking into account the complexity and number of requests, and provided you inform me of the extension '
      + 'and the reasons for it within the first month. Exercising this right is free of charge (Article 12(5)). If you do not take action '
      + 'on my request, you must inform me of the reasons within the same period (Article 12(4)).',
    confirm: 'Please confirm in writing that my data have been erased.',
    remedies:
      'If I do not receive a satisfactory reply within this period, I reserve the right to lodge a complaint with the competent supervisory '
      + 'authority (Article 77) and to seek an effective judicial remedy (Article 79).',
    closing: 'Yours faithfully,',
  },

  fr: {
    abbr: 'RGPD',
    recipient: "À l'attention du Délégué à la protection des données (DPO)",
    date: (formatted) => `Le ${formatted}`,
    subjectLabel: 'Objet :',
    refLabel: 'Réf. :',
    subject: (service, hasAccount) => `Demande d'effacement de données personnelles – article 17 du RGPD – ${hasAccount ? 'compte ' : ''}${service}`,
    greeting: 'Madame, Monsieur,',
    identity: (service, email, username) =>
      `Je suis titulaire d'un compte ${service} associé à l'adresse électronique ${email}${username ? ` (identifiant : ${username})` : ''}. `
      + "Ces éléments suffisent à m'identifier. En vertu de l'article 12, paragraphe 6, du RGPD, des informations complémentaires "
      + "ne peuvent m'être demandées qu'en cas de doute raisonnable sur mon identité, et dans la stricte mesure nécessaire pour la confirmer.",
    identityNoAccount: (service, email) =>
      `J'ai des raisons de penser que ${service} traite des données personnelles me concernant, notamment associées à l'adresse électronique ${email}. `
      + "Ces éléments suffisent à m'identifier. En vertu de l'article 12, paragraphe 6, du RGPD, des informations complémentaires "
      + "ne peuvent m'être demandées qu'en cas de doute raisonnable sur mon identité, et dans la stricte mesure nécessaire pour la confirmer.",
    listSeparator: ' ;',
    breachContext:
      "Ce compte figurant dans une fuite de données connue, je souhaite réduire au plus vite l'exposition de mes informations personnelles.",
    titles: ['1. Objet de la demande', '2. Motifs', '3. Mesures complémentaires demandées', '4. Délai de réponse', '5. Voies de recours'],
    request: (closeAccount) =>
      "Sur le fondement de l'article 17, paragraphe 1, du Règlement (UE) 2016/679 du 27 avril 2016 (Règlement général sur la protection "
      + "des données, « RGPD »), je vous demande d'effacer, dans les meilleurs délais, l'ensemble des données à caractère personnel me "
      + 'concernant que vous traitez, y compris les données dérivées, les profils, les segments marketing et les copies de sauvegarde, '
      + `${closeAccount ? 'et de clôturer le compte susmentionné' : 'ainsi que toute donnée me concernant obtenue auprès de tiers'}.`,
    groundsIntro: 'Cette demande repose sur les motifs suivants :',
    grounds: {
      no_longer_needed: (since) =>
        'les données ne sont plus nécessaires au regard des finalités pour lesquelles elles ont été collectées, '
        + `ce compte n'étant plus utilisé${since ? ` depuis ${since}` : ''} (article 17, paragraphe 1, point a), `
        + 'conformément au principe de limitation de la conservation (article 5, paragraphe 1, point e)',
      consent_withdrawn: () =>
        "je retire, avec effet immédiat, tout consentement que j'aurais pu donner au traitement de mes données "
        + "(article 7, paragraphe 3), et aucun autre fondement juridique ne justifie ce traitement (article 17, paragraphe 1, point b)",
      objection_legitimate_interest: () =>
        "je m'oppose, pour des raisons tenant à ma situation particulière, au traitement de mes données fondé sur votre intérêt "
        + "légitime (article 21, paragraphe 1). Il vous appartient de démontrer l'existence de motifs légitimes et impérieux prévalant "
        + "sur mes intérêts, droits et libertés ; à défaut, l'effacement s'impose (article 17, paragraphe 1, point c)",
      objection_marketing: () =>
        "je m'oppose à tout traitement de mes données à des fins de prospection, y compris le profilage qui y est lié "
        + "(article 21, paragraphes 2 et 3). Ce droit d'opposition est absolu et n'appelle aucune justification",
      unlawful: () => "mes données ont fait l'objet d'un traitement illicite (article 17, paragraphe 1, point d)",
      minor_at_signup: () =>
        "mes données ont été collectées dans le cadre de l'offre de services de la société de l'information alors que j'étais "
        + 'mineur(e) (article 17, paragraphe 1, point f, et article 8, paragraphe 1)',
    },
    restriction:
      "Dans l'attente de la vérification de vos éventuels motifs légitimes, je vous demande de limiter le traitement de mes données "
      + '(article 18, paragraphe 1, point d).',
    recipients:
      "Conformément à l'article 19, je vous demande de notifier cet effacement à chaque destinataire auquel mes données ont été "
      + "communiquées, et de m'indiquer l'identité de ces destinataires.",
    dataPublic:
      'Si vous avez rendu ces données publiques, je vous demande de prendre les mesures raisonnables pour informer les responsables '
      + "de traitement qui les exploitent de ma demande d'effacement de tout lien vers ces données, ainsi que de toute copie ou "
      + 'reproduction de celles-ci (article 17, paragraphe 2).',
    source:
      "Mes données n'ayant pas été collectées auprès de moi, je vous demande de m'indiquer leur source "
      + '(article 14, paragraphe 2, point f, et article 15, paragraphe 1, point g).',
    breach:
      "Ce compte figurant dans une fuite de données, je vous demande de m'indiquer si mes données ont été concernées et quelles "
      + "catégories de données étaient en cause. Lorsqu'une violation est susceptible d'engendrer un risque élevé pour mes droits "
      + "et libertés, vous êtes tenu de m'en informer (article 34).",
    exceptions:
      "Si vous estimez devoir conserver certaines données au titre d'une exception prévue à l'article 17, paragraphe 3, je vous "
      + "demande de m'indiquer précisément les données concernées, le fondement juridique invoqué et la durée de conservation. "
      + 'Les autres données doivent être effacées sans délai.',
    deadline:
      "Conformément à l'article 12, paragraphe 3, vous disposez d'un délai d'un mois à compter de la réception de la présente "
      + 'demande pour y donner suite. Ce délai ne peut être prolongé de deux mois que si cela est nécessaire, compte tenu de la '
      + "complexité et du nombre de demandes, et à condition de m'en informer, motifs à l'appui, dans le premier mois. L'exercice "
      + "de ce droit est gratuit (article 12, paragraphe 5). Si vous ne donnez pas suite à ma demande, vous êtes tenu de m'en "
      + 'communiquer les motifs dans ce même délai (article 12, paragraphe 4).',
    confirm: "Je vous remercie de me confirmer par écrit l'effacement effectif de mes données.",
    remedies:
      "À défaut de réponse satisfaisante dans le délai imparti, je me réserve le droit d'introduire une réclamation auprès de "
      + "la CNIL (www.cnil.fr) ou de toute autre autorité de contrôle compétente (article 77), ainsi que d'exercer un recours "
      + 'juridictionnel effectif (article 79).',
    closing: "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
  },

  es: {
    abbr: 'RGPD',
    recipient: 'A la atención del Delegado de Protección de Datos (DPD)',
    date: (formatted) => formatted,
    subjectLabel: 'Asunto:',
    refLabel: 'Ref.:',
    subject: (service, hasAccount) => `Solicitud de supresión de datos personales – artículo 17 del RGPD – ${hasAccount ? 'cuenta de ' : ''}${service}`,
    greeting: 'Estimados señores:',
    identity: (service, email, username) =>
      `Soy titular de una cuenta de ${service} asociada a la dirección de correo electrónico ${email}${username ? ` (nombre de usuario: ${username})` : ''}. `
      + 'Estos datos son suficientes para identificarme. De conformidad con el artículo 12, apartado 6, del RGPD, solo pueden '
      + 'solicitarme información adicional si tienen dudas razonables sobre mi identidad, y únicamente en la medida necesaria para confirmarla.',
    identityNoAccount: (service, email) =>
      `Tengo motivos para creer que ${service} trata datos personales que me conciernen, en particular datos asociados a la dirección de correo electrónico ${email}. `
      + 'Estos datos son suficientes para identificarme. De conformidad con el artículo 12, apartado 6, del RGPD, solo pueden '
      + 'solicitarme información adicional si tienen dudas razonables sobre mi identidad, y únicamente en la medida necesaria para confirmarla.',
    listSeparator: ';',
    breachContext:
      'Dado que esta cuenta figura en una violación de datos conocida, deseo reducir lo antes posible la exposición de mi información personal.',
    titles: ['1. Objeto de la solicitud', '2. Motivos', '3. Medidas adicionales solicitadas', '4. Plazo de respuesta', '5. Vías de recurso'],
    request: (closeAccount) =>
      'En virtud del artículo 17, apartado 1, del Reglamento (UE) 2016/679, de 27 de abril de 2016 (Reglamento General de Protección '
      + 'de Datos, «RGPD»), solicito la supresión sin dilación indebida de todos los datos personales que me conciernen y que ustedes '
      + `tratan, incluidos los datos derivados, los perfiles, los segmentos de marketing y las copias de seguridad${closeAccount ? ', así como el cierre de la cuenta mencionada' : ''}.`,
    groundsIntro: 'Esta solicitud se basa en los siguientes motivos:',
    grounds: {
      no_longer_needed: (since) =>
        'los datos ya no son necesarios en relación con los fines para los que fueron recogidos, '
        + `ya que la cuenta ${since ? `no se utiliza desde ${since}` : 'ya no se utiliza'} (artículo 17, apartado 1, letra a), `
        + 'conforme al principio de limitación del plazo de conservación (artículo 5, apartado 1, letra e)',
      consent_withdrawn: () =>
        'retiro, con efecto inmediato, cualquier consentimiento que haya podido otorgar para el tratamiento de mis datos '
        + '(artículo 7, apartado 3), y dicho tratamiento no se basa en ningún otro fundamento jurídico (artículo 17, apartado 1, letra b)',
      objection_legitimate_interest: () =>
        'me opongo, por motivos relacionados con mi situación particular, al tratamiento de mis datos basado en su interés legítimo '
        + '(artículo 21, apartado 1). Corresponde a ustedes acreditar motivos legítimos imperiosos que prevalezcan sobre mis intereses, '
        + 'derechos y libertades; en su defecto, los datos deben suprimirse (artículo 17, apartado 1, letra c)',
      objection_marketing: () =>
        'me opongo a cualquier tratamiento de mis datos con fines de mercadotecnia directa, incluida la elaboración de perfiles '
        + 'relacionada con dicha mercadotecnia (artículo 21, apartados 2 y 3). Este derecho es absoluto y no requiere justificación',
      unlawful: () => 'mis datos han sido tratados ilícitamente (artículo 17, apartado 1, letra d)',
      minor_at_signup: () =>
        'mis datos se obtuvieron en relación con la oferta de servicios de la sociedad de la información cuando era menor de edad '
        + '(artículo 17, apartado 1, letra f, y artículo 8, apartado 1)',
    },
    restriction:
      'Mientras se verifica si sus motivos legítimos prevalecen sobre los míos, solicito la limitación del tratamiento de mis datos '
      + '(artículo 18, apartado 1, letra d).',
    recipients:
      'De conformidad con el artículo 19, les ruego que comuniquen esta supresión a cada uno de los destinatarios a los que se hayan '
      + 'comunicado mis datos y que me informen sobre dichos destinatarios.',
    dataPublic:
      'Si ustedes han hecho públicos estos datos, les ruego que adopten medidas razonables para informar a los responsables que los '
      + 'estén tratando de mi solicitud de supresión de cualquier enlace a esos datos, o de cualquier copia o réplica de los mismos '
      + '(artículo 17, apartado 2).',
    source:
      'Dado que mis datos no se obtuvieron de mí, les ruego que me indiquen su origen '
      + '(artículo 14, apartado 2, letra f, y artículo 15, apartado 1, letra g).',
    breach:
      'Dado que esta cuenta figura en una violación de datos, les ruego que me indiquen si mis datos se vieron afectados y qué '
      + 'categorías de datos estaban en cuestión. Cuando una violación entrañe un alto riesgo para mis derechos y libertades, '
      + 'están obligados a comunicármela (artículo 34).',
    exceptions:
      'Si consideran que deben conservar determinados datos en virtud de alguna de las excepciones del artículo 17, apartado 3, '
      + 'les ruego que me indiquen con precisión qué datos, la base jurídica invocada y el plazo de conservación. Todos los demás '
      + 'datos deben suprimirse sin dilación.',
    deadline:
      'De conformidad con el artículo 12, apartado 3, disponen de un plazo de un mes a partir de la recepción de esta solicitud para '
      + 'atenderla. Dicho plazo solo podrá prorrogarse otros dos meses en caso necesario, teniendo en cuenta la complejidad y el número '
      + 'de solicitudes, y siempre que me informen de la prórroga y de sus motivos dentro del primer mes. El ejercicio de este derecho '
      + 'es gratuito (artículo 12, apartado 5). Si no dan curso a mi solicitud, deberán informarme de los motivos en el mismo plazo '
      + '(artículo 12, apartado 4).',
    confirm: 'Les ruego que me confirmen por escrito la supresión efectiva de mis datos.',
    remedies:
      'Si no recibo una respuesta satisfactoria en dicho plazo, me reservo el derecho de presentar una reclamación ante la autoridad '
      + 'de control competente (artículo 77) y de ejercer el derecho a la tutela judicial efectiva (artículo 79).',
    closing: 'Atentamente,',
  },
}

export function letterLanguage(code: string | undefined): LetterLanguage {
  const base = (code ?? '').slice(0, 2) as LetterLanguage
  return LETTER_LANGUAGES.includes(base) ? base : 'en'
}

function legalRefs(req: LetterRequest, abbr: string): string[] {
  const refs = ['17(1)', '12(6)']
  for (const ground of GROUND_ORDER) {
    if (req.grounds.includes(ground)) refs.push(...GROUND_REFS[ground])
  }
  refs.push('19')
  if (req.data_public) refs.push('17(2)')
  if (req.is_broker) refs.push('14(2)(f)', '15(1)(g)')
  if (req.breached) refs.push('34')
  refs.push('17(3)', '12(3)', '12(4)', '12(5)', '77', '79')
  return [...new Set(refs)].map((ref) => `${abbr} Art. ${ref}`)
}

export function buildLetter(req: LetterRequest, lang: LetterLanguage, today: Date = new Date()): Letter {
  const text = TEXTS[lang]
  const longDate = new Intl.DateTimeFormat(lang, { dateStyle: 'long' }).format(today)
  const since = req.inactive_since
    ? new Intl.DateTimeFormat(lang, { month: 'long', year: 'numeric' }).format(new Date(req.inactive_since))
    : null

  const grounds = GROUND_ORDER.filter((ground) => req.grounds.includes(ground))
    .map((ground) => `- ${text.grounds[ground](since)}`)
    .join(`${text.listSeparator}\n`)

  const measures = [
    req.grounds.includes('objection_legitimate_interest') && text.restriction,
    text.recipients,
    req.data_public && text.dataPublic,
    req.is_broker && text.source,
    req.breached && text.breach,
    text.exceptions,
  ].filter((measure): measure is string => Boolean(measure))
    .map((measure) => `- ${measure}`)
    .join('\n')

  const context = (req.context ?? (req.breached ? text.breachContext : '')).trim()
  const subject = text.subject(req.service_name, req.has_account)

  const blocks = [
    `${req.full_name}\n${req.account_email}`,
    [text.recipient, req.service_name, req.recipient_email].filter(Boolean).join('\n'),
    text.date(longDate),
    `${text.subjectLabel} ${subject}\n${text.refLabel} ${req.request_id}`,
    text.greeting,
    req.has_account
      ? text.identity(req.service_name, req.account_email, req.username)
      : text.identityNoAccount(req.service_name, req.account_email),
    context,
    `${text.titles[0]}\n\n${text.request(req.has_account)}`,
    grounds ? `${text.titles[1]}\n\n${text.groundsIntro}\n${grounds}.` : '',
    `${text.titles[2]}\n\n${measures}`,
    `${text.titles[3]}\n\n${text.deadline}\n\n${text.confirm}`,
    `${text.titles[4]}\n\n${text.remedies}`,
    text.closing,
    req.full_name,
  ]

  return {
    subject,
    body: blocks.filter(Boolean).join('\n\n'),
    recipient_email: req.recipient_email,
    contact_url: req.contact_url,
    legal_refs: legalRefs(req, text.abbr),
    generated_by: 'template',
    warnings: [],
  }
}

export function mockLetter(org: Organisation, fullName: string, email: string, lang: LetterLanguage): Letter {
  const grounds: Ground[] = ['consent_withdrawn', 'objection_marketing']
  if (org.type === 'broker') grounds.push('objection_legitimate_interest')

  return buildLetter({
    request_id: `TR-${org.id.toUpperCase()}`,
    full_name: fullName,
    account_email: email,
    service_name: org.site,
    username: null,
    has_account: org.type === 'social' || org.type === 'breach',
    recipient_email: `privacy@${org.domain}`,
    contact_url: `https://${org.domain}/privacy`,
    grounds,
    inactive_since: null,
    data_public: org.type === 'search' || org.type === 'social',
    is_broker: org.type === 'broker',
    breached: org.type === 'breach',
    context: null,
  }, lang)
}
