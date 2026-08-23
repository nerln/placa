// La misma página en los dos horarios del sistema.
// node gui/mirar/noche.mjs <url> <selector|-> <salida.png> [ancho] [alto]
import {abrir} from "./cdp.mjs";
const [url, sel, salida, ancho = 1280, alto = 900] = process.argv.slice(2);
for (const tema of ["light", "dark"]) {
  const p = await abrir({ancho: +ancho, alto: +alto, tema});
  await p.ir(url);
  if (sel !== "-") {
    await p.ev(`document.querySelector('${sel}')?.scrollIntoView({block:'start'}); 1`);
    await new Promise(r => setTimeout(r, 3500));
  }
  const ruta = salida.replace(/\.png$/, "-" + tema + ".png");
  await p.foto(ruta);
  console.log(ruta, "· fondo", await p.ev("getComputedStyle(document.body).backgroundColor"));
  await p.cerrar();
}
process.exit(0);
