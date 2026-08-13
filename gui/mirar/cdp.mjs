// Lo mínimo del protocolo de Chrome que hace falta acá.
export async function abrir({ancho = 1280, alto = 900, escala = 2, tema}) {
  const vs = await (await fetch("http://127.0.0.1:9333/json/new?about:blank",
                                {method: "PUT"})).json();
  const ws = new WebSocket(vs.webSocketDebuggerUrl);
  let n = 0; const esperando = new Map(); const errores = [];
  await new Promise(r => ws.onopen = r);
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.method === "Runtime.exceptionThrown")
      errores.push(m.params.exceptionDetails.exception?.description ||
                   m.params.exceptionDetails.text);
    if (esperando.has(m.id)) esperando.get(m.id)(m);
  };
  const cmd = (metodo, params = {}) => new Promise(r => {
    const i = ++n; esperando.set(i, r);
    ws.send(JSON.stringify({id: i, method: metodo, params}));
  });
  await cmd("Page.enable"); await cmd("Runtime.enable"); await cmd("Network.enable");
  // Sin esto Chrome sirve el datos.js de su caché y la foto miente.
  await cmd("Network.setCacheDisabled", {cacheDisabled: true});
  await cmd("Emulation.setDeviceMetricsOverride",
            {width: ancho, height: alto, deviceScaleFactor: escala, mobile: ancho < 600});
  if (tema) await cmd("Emulation.setEmulatedMedia",
                      {features: [{name: "prefers-color-scheme", value: tema}]});
  const ir = async url => {
    await cmd("Page.navigate", {url});
    await new Promise(r => setTimeout(r, 6500));
  };
  const ev = async expr => (await cmd("Runtime.evaluate",
    {expression: expr, awaitPromise: true, returnByValue: true})).result?.result?.value;
  const foto = async ruta => {
    const s = await cmd("Page.captureScreenshot", {format: "png"});
    const fs = await import("node:fs");
    fs.writeFileSync(ruta, Buffer.from(s.result.data, "base64"));
  };
  const cerrar = () => { ws.close(); };
  return {cmd, ir, ev, foto, cerrar, errores};
}
