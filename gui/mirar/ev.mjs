// node gui/mirar/ev.mjs <url> <expresion> [ancho]
import {abrir} from "./cdp.mjs";
const [url, expr, ancho = 1280] = process.argv.slice(2);
const p = await abrir({ancho: +ancho, escala: 1, movimiento: true});
await p.ir(url);
console.log(await p.ev(expr));
if (p.errores.length) console.log("ERRORES:\n" + p.errores.join("\n---\n"));
p.cerrar(); process.exit(0);
