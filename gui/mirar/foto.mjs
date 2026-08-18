// node gui/mirar/foto.mjs <url> <selector|-> <salida.png> [ancho] [alto] [tema]
import {abrir} from "./cdp.mjs";
const [url, sel, salida, ancho = 1280, alto = 900, tema] = process.argv.slice(2);
const p = await abrir({ancho: +ancho, alto: +alto, tema, movimiento: true});
await p.ir(url);
if (sel !== "-") {
  await p.ev(`document.querySelector('${sel}')?.scrollIntoView({block:'start'}); 1`);
  await new Promise(r => setTimeout(r, 3500));
}
await p.foto(salida);
console.log(salida, "· scrollY", await p.ev("Math.round(scrollY)"),
            p.errores.length ? "· ERRORES: " + p.errores.join(" | ") : "· sin errores");
p.cerrar(); process.exit(0);
