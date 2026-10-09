// Extrait du jeu (index.html) les listes de mots, phrases et histoires utilisées par les fiches PDF.
// Usage : node tools/donnees.js [graine] > donnees.json   (appelé automatiquement par tools/fiches.py)
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
let js = html.split('<script>')[1].split('</script>')[0];

// Hasard reproductible : même graine, mêmes fiches.
let seed = Number(process.argv[2] || 1) >>> 0;
Math.random = () => { seed = (seed + 0x6D2B79F5) >>> 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

// Le script du jeu touche au DOM en fin de fichier : on l'arrête juste avant les écrans.
js = js.replace('/* ================= Écrans', 'globalThis.__export = () => ({ LEX, GRAPH, SENTS, PROPER, NOUNS, HOMO, HOMO_HINT, IRREG, VERBS1, conj, NOUNS_A, ADJ, SUBJ_PP, TAGGED, TAGGED_P, SYN, ANT, PREF, FAMILLES, STORIES, KIDS, STUFF, CONF, misspell, NO_COUNT });\n/*');
const noop = () => ({});
global.document = { querySelector: () => ({ getContext: noop, addEventListener() {}, setAttribute() {}, style: {} }), querySelectorAll: () => [], addEventListener() {} };
global.window = { matchMedia: () => ({}) };
global.localStorage = { getItem: () => null, setItem() {} };
try { (0, eval)(js); } catch (e) { /* l'initialisation de l'interface échoue sans navigateur : sans importance ici */ }
const D = globalThis.__export();

const out = {
  lex: D.LEX.map(x => ({ w: x.w, syl: x.syl, sons: x.sons, fautes: D.misspell(x.w) })),
  noCount: D.NO_COUNT,
  graph: D.GRAPH.map(([pre, ans, post, bad, , rule]) => ({ pre, ans, post, bad, rule })),
  sents: D.SENTS, proper: D.PROPER,
  nouns: D.NOUNS.map(({ w, g, p }) => ({ w, g, p })),
  homo: D.HOMO, homoHint: D.HOMO_HINT,
  conj: {}, nounsA: D.NOUNS_A, adj: D.ADJ, subjPP: D.SUBJ_PP,
  tagged: D.TAGGED, taggedP: D.TAGGED_P, syn: D.SYN, ant: D.ANT, pref: D.PREF, familles: D.FAMILLES,
  kids: D.KIDS, stuff: D.STUFF, conf: D.CONF,
  stories: D.STORIES.map(f => Array.from({ length: 4 }, () => f()))
};
for (const v of [...D.VERBS1, ...Object.keys(D.IRREG)]) {
  out.conj[v] = {};
  for (const t of ['pr', 'im', 'fu', 'pc']) out.conj[v][t] = D.conj(v, t, false);
  out.conj[v].pcF = D.conj(v, 'pc', true);
}
process.stdout.write(JSON.stringify(out));
