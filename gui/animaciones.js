// SPDX-FileCopyrightText: 2026 Eugenio Nerelli
// SPDX-License-Identifier: Apache-2.0
const montarAnimaciones = (function(){
let DATOS_PAGINA = {jugadores:[], mu:{}, psi:{}, pgana:{}};
/* ==========================================================================
   Un Manim chiquito, en el navegador.

   Las tres animaciones que explican el modelo no son video: se dibujan en vivo
   sobre un canvas, con la misma gramática que usa Manim (una línea de tiempo,
   FadeIn con desplazamiento, Write que va apareciendo, Create que traza el
   camino, LaggedStart que escalona). Renderizar video habría sido más fácil,
   pero un MP4 pesa, se ve borroso al escalar y no se adapta al ancho del
   teléfono. Esto se dibuja a la resolución real del aparato, pesa unos kilos y
   se puede pausar y arrastrar.

   El espacio de trabajo es de 100x100 unidades y se mapea al tamaño del lienzo,
   así la misma escena entra igual en un teléfono que en un monitor.
   ========================================================================== */

const suave = p => p * p * (3 - 2 * p);                 // el "smooth" de Manim
const salida = p => 1 - Math.pow(1 - p, 3);
const lerp = (a, b, p) => a + (b - a) * p;
const clamp01 = p => p < 0 ? 0 : p > 1 ? 1 : p;

class Objeto {
  constructor(o = {}) {
    Object.assign(this, {x:50, y:50, op:1, k:1, dx:0, dy:0, visible:false, z:0}, o);
  }
  dibujar(){}
}

class Texto extends Objeto {
  constructor(o){ super(Object.assign({tam:4, color:"#F4F2EC", peso:400, alinear:"center", prog:1, mono:false, display:false}, o)); }
  fuente(u){
    const px = this.tam * u * this.k;
    const fam = this.mono ? 'ui-monospace,Menlo,Consolas,monospace'
                          : this.display ? '"Bodoni",Georgia,serif'
                          : '"Atkinson",-apple-system,system-ui,sans-serif';
    return `${this.peso} ${px}px ${fam}`;
  }
  dibujar(c, u, ox, oy){
    const lineas = String(this.txt).split("\n");
    c.font = this.fuente(u);
    c.textAlign = this.alinear;
    c.textBaseline = "middle";
    c.globalAlpha = this.op;
    c.fillStyle = this.color;
    const alto = this.tam * u * 1.32 * this.k;
    const y0 = oy + (this.y + this.dy) * u - (lineas.length - 1) * alto / 2;
    lineas.forEach((l, i) => {
      const n = this.prog >= 1 ? l : l.slice(0, Math.ceil(l.length * this.prog));
      c.fillText(n, ox + (this.x + this.dx) * u, y0 + i * alto);
    });
    c.globalAlpha = 1;
  }
  ancho(c, u){ c.font = this.fuente(u);
    return Math.max(...String(this.txt).split("\n").map(l => c.measureText(l).width)); }
}

class Linea extends Objeto {
  constructor(o){ super(Object.assign({x2:50, y2:50, color:"#949BAD", ancho:0.28, prog:1, guion:null}, o)); }
  dibujar(c, u, ox, oy){
    c.globalAlpha = this.op;
    c.strokeStyle = this.color;
    c.lineWidth = Math.max(1, this.ancho * u);
    c.lineCap = "round";
    if(this.guion) c.setLineDash(this.guion.map(v => v * u));
    const X1 = ox + (this.x + this.dx) * u, Y1 = oy + (this.y + this.dy) * u;
    const X2 = ox + (this.x2 + this.dx) * u, Y2 = oy + (this.y2 + this.dy) * u;
    c.beginPath(); c.moveTo(X1, Y1);
    c.lineTo(lerp(X1, X2, this.prog), lerp(Y1, Y2, this.prog));
    c.stroke(); c.setLineDash([]); c.globalAlpha = 1;
  }
}

class Marco extends Objeto {
  constructor(o){ super(Object.assign({w:20, h:10, color:"#C9A227", ancho:0.28, r:1, prog:1}, o)); }
  dibujar(c, u, ox, oy){
    const X = ox + (this.x + this.dx - this.w/2) * u, Y = oy + (this.y + this.dy - this.h/2) * u;
    const W = this.w * u, H = this.h * u, R = this.r * u;
    c.globalAlpha = this.op; c.strokeStyle = this.color;
    c.lineWidth = Math.max(1, this.ancho * u);
    const per = 2 * (W + H);
    c.setLineDash([per * this.prog, per]);
    c.beginPath(); c.roundRect(X, Y, W, H, R); c.stroke();
    c.setLineDash([]); c.globalAlpha = 1;
  }
}

class Barra extends Objeto {
  constructor(o){ super(Object.assign({w:10, h:5, color:"#494F58", prog:1, r:0.5}, o)); }
  dibujar(c, u, ox, oy){
    const X = ox + (this.x + this.dx) * u, Y = oy + (this.y + this.dy) * u;
    const W = Math.max(this.w * u * this.prog, 0), Hh = this.h * u;
    c.globalAlpha = this.op; c.fillStyle = this.color;
    c.beginPath(); c.roundRect(X, Y, W, Hh, Math.min(this.r*u, W/2, Hh/2)); c.fill();
    c.globalAlpha = 1;
  }
}

class Punto extends Objeto {
  constructor(o){ super(Object.assign({r:1.1, color:"#F0D274", brillo:false}, o)); }
  dibujar(c, u, ox, oy){
    const X = ox + (this.x + this.dx) * u, Y = oy + (this.y + this.dy) * u, R = this.r * this.k * u;
    c.globalAlpha = this.op;
    if(this.brillo){
      const g = c.createRadialGradient(X, Y, 0, X, Y, R * 3.4);
      g.addColorStop(0, "rgba(240,210,116,.5)"); g.addColorStop(1, "rgba(240,210,116,0)");
      c.fillStyle = g; c.beginPath(); c.arc(X, Y, R * 3.4, 0, 7); c.fill();
    }
    c.fillStyle = this.color; c.beginPath(); c.arc(X, Y, R, 0, 7); c.fill();
    c.globalAlpha = 1;
  }
}

/* -------------------------------------------------------------------------- */

class Escena {
  constructor(){ this.objs = []; this.pistas = []; this.reloj = 0; }
  add(...o){ o.forEach(x => this.objs.push(x)); return o[0]; }

  pista(o, dur, fn, retraso = 0){
    const t0 = this.reloj + retraso;
    this.pistas.push({t0, t1: t0 + dur, o, fn});
    return t0 + dur;
  }
  play(anims, dur = 0.7){
    const lista = Array.isArray(anims) ? anims : [anims];
    let fin = this.reloj;
    lista.forEach(a => { fin = Math.max(fin, a(this, dur, 0)); });
    this.reloj = fin;
    return this;
  }
  escalonado(anims, dur = 0.7, lag = 0.14){
    let fin = this.reloj;
    anims.forEach((a, i) => { fin = Math.max(fin, a(this, dur, i * lag)); });
    this.reloj = fin;
    return this;
  }
  esperar(t){ this.reloj += t; return this; }

  render(c, u, ox, oy, t){
    this.objs.forEach(o => { o.op = o._op0 ?? 0; });
    this.pistas.forEach(p => {
      if(t < p.t0) return;
      const q = clamp01((t - p.t0) / Math.max(p.t1 - p.t0, 1e-6));
      p.fn(p.o, q);
    });
    [...this.objs].sort((a,b) => (a.z||0) - (b.z||0))
      .forEach(o => { if(o.visible && o.op > 0.002) o.dibujar(c, u, ox, oy); });
  }
  get duracion(){ return this.pistas.reduce((m,p) => Math.max(m, p.t1), 0) + 1.6; }
}

/* --- animaciones, con la firma (escena, dur, retraso) --> tiempo final ----- */
const aparecer = (o, dy = 2) => (s, d, r) => {
  o._op0 = 0;
  return s.pista(o, d, (x, p) => { x.visible = true; x.op = suave(p); x.dy = lerp(dy, 0, suave(p)); }, r);
};
const desaparecer = o => (s, d, r) =>
  s.pista(o, d, (x, p) => { x.visible = true; x.op = 1 - suave(p); }, r);
const escribir = o => (s, d, r) => {
  o._op0 = 0;
  return s.pista(o, d, (x, p) => { x.visible = true; x.op = 1; x.prog = salida(p); }, r);
};
const trazar = o => (s, d, r) => {
  o._op0 = 0;
  return s.pista(o, d, (x, p) => { x.visible = true; x.op = 1; x.prog = suave(p); }, r);
};
const surgir = (o, k0 = 0.3) => (s, d, r) => {
  o._op0 = 0;
  return s.pista(o, d, (x, p) => { x.visible = true; x.op = suave(p); x.k = lerp(k0, o._k ?? 1, salida(p)); }, r);
};
const trasladar = (o, x, y, k) => (s, d, r) => {
  const x0 = o.x, y0 = o.y, k0 = o.k;
  return s.pista(o, d, (t, p) => {
    t.visible = true; t.op = 1;
    t.x = lerp(x0, x ?? x0, suave(p));
    t.y = lerp(y0, y ?? y0, suave(p));
    if(k != null) t.k = lerp(k0, k, suave(p));
  }, r);
};
const crecer = o => (s, d, r) => {
  o._op0 = 0;
  return s.pista(o, d, (x, p) => { x.visible = true; x.op = 1; x.prog = suave(p); }, r);
};
const sostener = o => (s, d, r) => s.pista(o, d, (x) => { x.visible = true; x.op = 1; }, r);
const tenir = (o, col) => (s, d, r) => s.pista(o, d, (x, p) => {
  x.visible = true; x.op = 1; if(p > 0.5) x.color = col; }, r);

/* ==========================================================================
   Las tres piezas.

   No son demos: cada una es un gráfico que se puede leer cuando termina de
   dibujarse. La animación existe para mostrar de dónde sale cada número, no
   para decorar. Los colores son los mismos del resto de la página: rojo el voto
   para eliminar, azul el voto para salvar.
   ========================================================================== */
/* Los colores salen del tema de la página, no de constantes: si el sistema pasa
   a oscuro, las escenas se reconstruyen con la paleta nueva. */
let ROJO, AZUL, TIN, TIN2, TIN3, CARRIL;
function leerPaleta(){
  const v = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  ROJO = v("--rechazo-txt") || "#B3122F";
  AZUL = v("--apoyo-txt")   || "#0070A3";
  TIN  = v("--tinta")       || "#14161A";
  TIN2 = v("--tinta2")      || "#494F58";
  TIN3 = v("--tinta3")      || "#606874";
  CARRIL = v("--sup3")      || "#E7EAEE";
}

/* --- 1. El reparto real de una gala, como barra apilada ------------------- */
function escenaIdentidad(){
  leerPaleta();
  const s = new Escena();
  const DATOS = [["Luana",0.1],["Juanicar",0.3],["Hanssen",0.5],["Majluf",0.9],["Sol",46.7],["Campanita",53.3]];
  const total = DATOS.reduce((a,[,v])=>a+v,0);                 // 101,8

  s.add(new Texto({txt:"Gala 27 · 3 de agosto", x:6, y:8, tam:4.4, color:TIN, peso:700,
                   alinear:"left", display:true, visible:true, _op0:1}));
  const sub = s.add(new Texto({txt:"reparto del voto para eliminar, como lo publicó Telefe",
                               x:6, y:14, tam:3, color:TIN3, alinear:"left"}));
  s.play(aparecer(sub, -1), .4);

  // barra apilada: cada tramo es proporcional a su porcentaje publicado
  const X0 = 6, ANCHO = 88, Y = 26, ALTO = 9;
  const carril = s.add(new Marco({x:X0+ANCHO/2, y:Y+ALTO/2, w:ANCHO, h:ALTO, color:CARRIL, ancho:.5, r:.6}));
  s.play(trazar(carril), .4);

  let acum = 0;
  const tramos = DATOS.map(([n,v]) => {
    const w = ANCHO * v/total, x = X0 + ANCHO*acum/total; acum += v;
    const r = s.add(new Barra({x, y:Y, w, h:ALTO, color: v>40 ? ROJO : TIN2}));
    const et = s.add(new Texto({txt:n, x:x+w/2, y:Y-3.4, tam:2.7, color:TIN2}));
    const va = s.add(new Texto({txt:String(v).replace(".",",")+"%", x:x+w/2, y:Y+ALTO+4.2,
                                tam:2.9, color: v>40 ? ROJO : TIN2, peso:700, mono:true}));
    return {r, et, va, ancho:w};
  });
  s.escalonado(tramos.map(t => crecer(t.r)), .45, .13);
  s.escalonado(tramos.filter(t=>t.ancho>7).flatMap(t => [aparecer(t.et,0), aparecer(t.va,0)]), .3, .05);
  s.esperar(.6);

  // la suma no da 100
  const suma = s.add(new Texto({txt:"suman 101,8 %", x:50, y:47, tam:4.6, color:TIN, peso:700, display:true}));
  s.play(aparecer(suma, -1.5), .5).esperar(.9);

  // el mano a mano se reparte sobre el residuo
  const marco = s.add(new Marco({x:X0 + ANCHO*(1 - (46.7+53.3)/total/2), y:Y+ALTO/2,
                                 w:ANCHO*(46.7+53.3)/total, h:ALTO+3, color:ROJO, ancho:.4, r:.8}));
  const nota = s.add(new Texto({txt:"el mano a mano se renormaliza al 100 %\nsobre lo que quedaba sin repartir",
                                x:50, y:58, tam:3.1, color:ROJO}));
  s.play([trazar(marco), aparecer(nota)], .55).esperar(1.6);
  s.play([desaparecer(marco), desaparecer(nota), desaparecer(suma)], .4);

  // la identidad, escrita
  const eq1 = s.add(new Texto({txt:"101,8 − 100 = 1,8", x:50, y:50, tam:5, color:TIN, peso:700, display:true}));
  s.play(escribir(eq1), .7).esperar(.4);
  const marco2 = s.add(new Marco({x:X0 + ANCHO*(1.8/total)/2, y:Y+ALTO/2,
                                  w:Math.max(ANCHO*1.8/total, 2.4), h:ALTO+3, color:AZUL, ancho:.4, r:.6}));
  const eq2 = s.add(new Texto({txt:"0,1 + 0,3 + 0,5 + 0,9 = 1,8", x:50, y:59, tam:4, color:AZUL, peso:700, mono:true}));
  s.play(trazar(marco2), .5);
  s.play(escribir(eq2), .7).esperar(.5);

  const fin = s.add(new Texto({txt:"Cuadra. En esa placa no faltaba nadie:\nes el reparto completo de la noche.",
                               x:50, y:72, tam:3.5, color:TIN2}));
  s.play(aparecer(fin), .5).esperar(1.5);
  return s;
}

/* --- 2. Las dos escalas, como gráfico de pendiente ------------------------ */
function escenaDosEscalas(){
  leerPaleta();
  const s = new Escena();
  const J = DATOS_PAGINA.jugadores;
  const porMu  = [...J].sort((a,b) => DATOS_PAGINA.mu[a]  - DATOS_PAGINA.mu[b]);   // menos rechazo primero
  const porPsi = [...J].sort((a,b) => DATOS_PAGINA.psi[b] - DATOS_PAGINA.psi[a]);  // más apoyo primero
  const fila = n => 21 + n * 6.6;

  s.add(new Texto({txt:"Las dos escalas, jugadora por jugadora", x:50, y:7, tam:4.4,
                   color:TIN, peso:700, display:true, visible:true, _op0:1}));
  const iz = s.add(new Texto({txt:"MENOS RECHAZO", x:19, y:15, tam:2.7, color:ROJO, peso:700}));
  const de = s.add(new Texto({txt:"MÁS APOYO", x:81, y:15, tam:2.7, color:AZUL, peso:700}));
  s.play([aparecer(iz,-1), aparecer(de,-1)], .4);

  const izq = porMu.map((n,i) => s.add(new Texto({txt:n, x:19, y:fila(i), tam:3.1, color:TIN2})));
  s.escalonado(izq.map(t => aparecer(t, 0)), .3, .05);
  const der = porPsi.map((n,i) => s.add(new Texto({txt:n, x:81, y:fila(i), tam:3.1, color:TIN2})));
  s.escalonado(der.map(t => aparecer(t, 0)), .3, .05);
  s.esperar(.3);

  // una línea por persona: si las dos escalas fueran la misma, saldrían planas
  const lineas = porMu.map((n,i) => {
    const j = porPsi.indexOf(n);
    const salto = Math.abs(i - j);
    return s.add(new Linea({x:27, y:fila(i), x2:73, y2:fila(j), ancho:.32,
      color: salto >= 4 ? ROJO : salto >= 2 ? TIN2 : "#C7CCD3"}));
  });
  s.escalonado(lineas.map(l => trazar(l)), .5, .09);
  s.esperar(.8);

  const obs = s.add(new Texto({txt:"Si las dos escalas midieran lo mismo,\nlas líneas saldrían planas.",
                               x:50, y:93.5, tam:3.1, color:TIN2}));
  s.play(aparecer(obs), .5).esperar(1.8);
  s.play(desaparecer(obs), .35);

  const caso = s.add(new Texto({txt:"Hanssen es el menos rechazado de la casa\ny el octavo en apoyo. Ese cruce decide la final.",
                                x:50, y:93.5, tam:3.1, color:ROJO, peso:700}));
  s.play(aparecer(caso), .5).esperar(2.2);
  return s;
}

/* --- 3. Monte Carlo: las corridas se apilan hasta formar el gráfico ------- */
function escenaMonteCarlo(){
  leerPaleta();
  const s = new Escena();
  const J = [...DATOS_PAGINA.jugadores].sort((a,b) => DATOS_PAGINA.pgana[b] - DATOS_PAGINA.pgana[a]);
  const pmax = Math.max(...J.map(n => DATOS_PAGINA.pgana[n]));

  s.add(new Texto({txt:"120.000 temporadas simuladas", x:50, y:7, tam:4.4, color:TIN,
                   peso:700, display:true, visible:true, _op0:1}));
  const sub = s.add(new Texto({txt:"cada corrida juega las eliminaciones que faltan y anota quién gana",
                               x:50, y:13, tam:2.8, color:TIN3}));
  s.play(aparecer(sub,-1), .4);

  const X0 = 29, ANCHO = 54, fila = i => 21 + i*6.6;
  const nombres = J.map((n,i) => s.add(new Texto({txt:n, x:27, y:fila(i), tam:3.1,
                                                  color:TIN2, alinear:"right"})));
  s.escalonado(nombres.map(t => aparecer(t,0)), .28, .045);

  // las barras crecen a la vez, como si se fueran contando las corridas
  const barras = J.map((n,i) => s.add(new Barra({
    x:X0, y:fila(i)-2.6, w:ANCHO*DATOS_PAGINA.pgana[n]/pmax, h:5.2,
    color: i===0 ? ROJO : TIN2})));
  const cifras = J.map((n,i) => s.add(new Texto({
    txt:(100*DATOS_PAGINA.pgana[n]).toFixed(1).replace(".",",")+"%",
    x:X0 + ANCHO*DATOS_PAGINA.pgana[n]/pmax + 2, y:fila(i), tam:3, mono:true,
    color: i===0 ? ROJO : TIN3, alinear:"left", peso:700})));
  s.play(barras.map(b => crecer(b)), 1.5);
  s.escalonado(cifras.map(c => aparecer(c,0)), .3, .05);
  s.esperar(.9);

  // El nombre sale del dato, no escrito a mano: cuando cambia la favorita esta
  // frase cambiaba de significado sin cambiar de texto, y quedaba nombrando a
  // quien ya no lidera.
  const fin = s.add(new Texto({txt:"No es que "+J[0]+" vaya a ganar.\nEs que gana más veces que cualquier otra.",
                               x:50, y:94, tam:3.2, color:TIN, peso:700}));
  s.play(aparecer(fin), .5).esperar(1.8);
  return s;
}

/* ==========================================================================
   Reproductor
   ========================================================================== */
function montarAnimaciones(raiz, quieto, datos){
  DATOS_PAGINA = datos;
  const CAPS = [
    {id:"identidad", nom:"El reparto de una gala", crear:escenaIdentidad,
     pie:"Cómo se lee una gala entera y por qué una resta prueba que la placa estaba completa."},
    {id:"escalas", nom:"Las dos escalas", crear:escenaDosEscalas,
     pie:"Cada línea es una jugadora. Cuanto más inclinada, más distinto la trata cada votación."},
    {id:"montecarlo", nom:"Las 120.000 corridas", crear:escenaMonteCarlo,
     pie:"De dónde sale cada porcentaje del pronóstico."},
  ];

  raiz.innerHTML =
    '<div class="anim-tabs" role="tablist"></div>' +
    '<div class="anim-lienzo"><canvas></canvas></div>' +
    '<div class="anim-mandos">' +
      '<button class="btn-gala anim-play" type="button" aria-label="Reproducir">▶</button>' +
      '<input class="anim-barra" type="range" min="0" max="1000" value="0" aria-label="Posición de la animación">' +
      '<span class="anim-t mono">0,0s</span>' +
    '</div><p class="anim-pie"></p>';

  const tabs = raiz.querySelector(".anim-tabs");
  const cv = raiz.querySelector("canvas");
  const ctx = cv.getContext("2d");
  const btn = raiz.querySelector(".anim-play");
  const barra = raiz.querySelector(".anim-barra");
  const reloj = raiz.querySelector(".anim-t");
  const pie = raiz.querySelector(".anim-pie");

  let esc = null, dur = 1, t = 0, corriendo = false, ultimo = 0, actual = -1, raf = null;

  CAPS.forEach((c, i) => {
    const b = document.createElement("button");
    b.className = "anim-tab"; b.type = "button"; b.textContent = c.nom;
    b.setAttribute("role","tab");
    b.onclick = () => elegir(i, true);
    tabs.appendChild(b);
  });

  function medir(){
    const r = raiz.querySelector(".anim-lienzo").getBoundingClientRect();
    if(r.width < 40) return false;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    cv.width = r.width * dpr; cv.height = r.height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return true;
  }
  function pintar(){
    if(!esc) return;                       // el reintento de medida corre antes de elegir capítulo
    const r = raiz.querySelector(".anim-lienzo").getBoundingClientRect();
    ctx.clearRect(0, 0, r.width, r.height);
    const u = Math.min(r.width, r.height) / 100;
    esc.render(ctx, u, (r.width - 100 * u) / 2, (r.height - 100 * u) / 2, t);
    barra.value = Math.round(1000 * t / dur);
    reloj.textContent = t.toFixed(1).replace(".", ",") + "s";
  }
  function lazo(ahora){
    raf = null;
    const dt = Math.min((ahora - ultimo) / 1000, 0.05);
    ultimo = ahora;
    if(corriendo){
      t += dt;
      if(t >= dur){ t = dur; parar(); }
    }
    pintar();
    if(corriendo) raf = requestAnimationFrame(lazo);
  }
  function arrancar(){
    if(document.visibilityState !== "visible"){ t = dur; parar(); pintar(); return; }
    if(t >= dur - 0.01) t = 0;
    corriendo = true; btn.textContent = "❚❚"; btn.setAttribute("aria-label","Pausar");
    ultimo = performance.now();
    if(!raf) raf = requestAnimationFrame(lazo);
    // misma garantía que en el otro lienzo: con la pestaña en segundo plano
    // requestAnimationFrame se estrangula y el gráfico quedaría a medias
    clearTimeout(arrancar._g);
    arrancar._g = setTimeout(() => { if(corriendo){ t = dur; parar(); pintar(); } }, (dur + 1.5) * 1000);
  }
  function parar(){
    corriendo = false; btn.textContent = "▶"; btn.setAttribute("aria-label","Reproducir");
  }
  function elegir(i, reproducir){
    if(i === actual) { t = 0; if(reproducir) arrancar(); return; }
    actual = i;
    [...tabs.children].forEach((b, k) => b.setAttribute("aria-selected", k === i));
    esc = CAPS[i].crear();
    dur = esc.duracion; t = 0;
    pie.textContent = CAPS[i].pie;
    medir(); pintar();
    if(reproducir && !quieto) arrancar(); else parar();
  }

  btn.addEventListener("click", () => corriendo ? parar() : arrancar());
  barra.addEventListener("input", () => { parar(); t = dur * barra.value / 1000; pintar(); });

  elegir(0, false);

  if(typeof alCambiarTema === "function"){
    alCambiarTema(() => { const i = actual; actual = -1; elegir(i, false); });
  }

  let intentos = 0;
  (function reintentar(){ if(medir()){ pintar(); return; } if(intentos++ < 30) setTimeout(reintentar, 120); })();
  new ResizeObserver(() => { if(medir()) pintar(); }).observe(raiz.querySelector(".anim-lienzo"));

  // arranca sola la primera vez que entra en pantalla, y se pausa al salir
  if(!quieto && "IntersectionObserver" in window){
    let yaArranco = false;
    new IntersectionObserver(es => es.forEach(e => {
      if(e.isIntersecting && !yaArranco){ yaArranco = true; arrancar(); }
      else if(!e.isIntersecting && corriendo) parar();
    }), {threshold:.45}).observe(raiz);
  }
}

return montarAnimaciones;
})();
