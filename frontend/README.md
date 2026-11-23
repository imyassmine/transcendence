React + TypeScript + Vite + Tailwind.

npm install
npm run dev     # http://localhost:5173, /api is proxied to localhost:8000
npm run build
npm run lint

pages/              one file per page (routes in App.tsx)
components/ui/      Button, Card, TextField
components/layout   the header around the pages
utils/              api.ts 

style: use the token classes only (bg-surface, text-muted, border-border,
bg-accent, font-mono, rounded-box, no raw colours like bg-gray-100)
