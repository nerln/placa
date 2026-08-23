// La comprobación del RENDER, que es la que faltaba.
//
// Las diez comprobaciones de verificar.py validan los datos, y por eso ninguna
// vio nunca esta clase de rotura: un texto que se arma en el navegador con un
// campo vacío y deja «. .» en pantalla, un «Son 0 puntos» que sale de redondear
// una diferencia de décimas, un NaN, o una celda que empuja el documento y
// pone scroll lateral en el teléfono. Ningún dato está mal en esos casos: lo
// roto es la página armada.
//
// Esto abre web/index.html en el Chrome sin ventana, lo mira como lo miraría
// una persona, y falla con salida distinta de cero si encuentra:
//
//   * NaN, undefined o [object en el texto visible
//   * puntuación huérfana: «. .», «: .», «; .», paréntesis vacíos
//   * una diferencia redondeada a cero («Son 0 puntos»)
//   * desborde lateral del documento a 320, 360, 390, 414 y 1280 px
//
// Lo llama bin/publicar.sh antes de empujar. Si no hay Chrome en la máquina
// (la nube de las routines no lo tiene), publicar.sh lo salta y lo dice, igual
// que verificar.py salta la comprobación de sintaxis cuando no hay node.
//
//   node gui/mirar/comprobar.mjs [ruta-a-index.html]

import {abrir} from "./cdp.mjs";
import {pathToFileURL} from "node:url";
import {resolve} from "node:path";

const ruta = process.argv[2] || "web/index.html";
const url = pathToFileURL(resolve(ruta)).href;

const PATRONES = [
  [/NaN/, "NaN en el texto visible"],
  [/undefined/, "undefined en el texto visible"],
  [/\[object/, "[object en el texto visible"],
  [/\.\s+\./, "dos puntos finales seguidos («. .»), señal de un campo vacío"],
  [/:\s*[.;,]/, "dos puntos seguidos de puntuación («: .»), señal de una lista vacía"],
  [/;\s*\./, "punto y coma seguido de punto («; .»)"],
  [/\(\s*\)/, "paréntesis vacíos"],
  [/\bSon 0(,0)? puntos\b/, "una diferencia redondeada a cero («Son 0 puntos»)"],
  [/\bde la ventana de\s*\./, "una ventana sin valor"],
];

const ANCHOS = [320, 360, 390, 414, 1280];

let fallos = 0;
const fallo = m => { console.log("  FALLA · " + m); fallos += 1; };

// --- el texto, una sola vez a ancho de escritorio ---------------------------
{
  const p = await abrir({ancho: 1280, alto: 900, escala: 1});
  await p.ir(url);
  // El texto visible, con el contexto de cada hallazgo para poder ir derecho.
  const texto = await p.ev("document.body.innerText");
  for (const [rx, que] of PATRONES) {
    const m = (texto || "").match(rx);
    if (m) {
      const i = texto.indexOf(m[0]);
      const ctx = texto.slice(Math.max(0, i - 60), i + 60).replace(/\s+/g, " ");
      fallo(que + "\n    …" + ctx + "…");
    }
  }
  if (p.errores.length)
    fallo("errores de JavaScript al cargar:\n    " + p.errores[0].split("\n")[0]);
  if (!fallos) console.log("  ok · el texto visible no tiene restos de armado");
  await p.cerrar();
}

// --- el desborde, a cada ancho ---------------------------------------------
for (const w of ANCHOS) {
  const p = await abrir({ancho: w, alto: 900, escala: 1});
  await p.ir(url);
  const r = await p.ev(
    "JSON.stringify({sw: document.documentElement.scrollWidth, " +
    "cw: document.documentElement.clientWidth})");
  const {sw, cw} = JSON.parse(r || "{}");
  if (sw > cw + 1) {
    // quien empuja, descartando lo que vive dentro de un contenedor que recorta
    const quien = await p.ev(`(function(){
      var W=document.documentElement.clientWidth;
      function clipado(e){for(var q=e.parentElement;q&&q!==document.body;q=q.parentElement){
        var o=getComputedStyle(q).overflowX;
        if(o==='auto'||o==='scroll'||o==='hidden')return true}return false}
      var peor=null;
      document.querySelectorAll('body *').forEach(function(e){
        var r=e.getBoundingClientRect();
        if(r.width<2||r.height<2||r.right<=W+1||clipado(e))return;
        if(!peor||r.right>peor.der)peor={der:Math.round(r.right),
          quien:(e.id||e.className||e.tagName).toString().slice(0,50),
          sec:(e.closest('section')||{}).id||''};
      });
      return JSON.stringify(peor);
    })()`);
    fallo("desborde a " + w + "px: documento de " + sw + "px · " + quien);
  } else {
    console.log("  ok · sin desborde a " + w + "px");
  }
  await p.cerrar();
}

if (fallos) {
  console.log("\n" + fallos + " fallo(s) de render: no se publica");
  process.exit(1);
}
console.log("\nel render cierra");
process.exit(0);
