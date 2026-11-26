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

export function mockLetter(org: Organisation, fullName: string, email: string): Letter {
  return {
    subject: 'Request for erasure of personal data (Article 17 GDPR)',
    body: [
      'Dear Data Protection Officer,',
      '',
      `I am writing to request the erasure of all personal data concerning me held by ${org.site}, under Article 17 of the General Data Protection Regulation (GDPR).`,
      '',
      `Email linked to my data: ${email}`,
      '',
      'I withdraw any consent I may have given, and I object to any processing of my data for direct marketing purposes (Article 21(2) GDPR).',
      '',
      'Please confirm the erasure within one month of receiving this request, as required by Article 12(3) GDPR. Without an answer, I may lodge a complaint with the competent supervisory authority.',
      '',
      'Yours faithfully,',
      fullName,
    ].join('\n'),
    recipient_email: `privacy@${org.domain}`,
    contact_url: `https://${org.domain}/privacy`,
    legal_refs: ['GDPR Art. 17', 'GDPR Art. 21(2)', 'GDPR Art. 12(3)'],
    generated_by: 'template',
    warnings: [],
  }
}
