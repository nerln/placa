"""
ETAPA 1-bis - Logit condicional DINAMICO (state-space).

El ajuste estatico falla de forma sistematica: el mismo jugador pasa del 38,45%
de voto negativo (Luana, gala 23) al 0,10% (gala 27) en tres semanas, y ninguna
recomposicion de placa explica esa caida bajo un theta constante. El rechazo del
publico NO es un rasgo fijo: deriva semana a semana segun el relato del programa.

Modelo (equivalente al de agregacion de encuestas en pronostico electoral):

    estado      theta[i, t]                   (rechazo latente del jugador i en t)
    transicion  theta[i,t+1] - theta[i,t] ~ N(0, sigma^2 * dt_semanas)
    observacion logit condicional multinomial sobre la placa de la gala t

Se estima el modo posterior (MAP) con gradientes analiticos, y sigma se elige
por VALIDACION CRUZADA dejando una gala afuera: es el dato el que decide cuanta
deriva hay, y ese mismo sigma alimenta despues la simulacion Monte Carlo.

Identificacion: theta esta definido salvo una constante por corte temporal, asi
que cada corte se centra en cero.
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent.parent
HOY = date(2026, 8, 8)
FECHA_GALA28 = "2026-08-10"


def _d(f: str) -> date:
    y, m, dd = (int(x) for x in f.split("-"))
    return date(y, m, dd)


def cargar():
    return json.loads((ROOT / "data" / "galas.json").read_text())


# ---------------------------------------------------------------------------

class ModeloDinamico:
    def __init__(self, cfg, sigma=0.9, n_eff=400.0, n_eff_encuesta=90.0,
                 usar_encuesta=True, sigma0=2.5, excluir_gala=None,
                 hasta_gala=None):
        self.cfg = cfg
        self.sigma = sigma
        self.sigma0 = sigma0
        self.n_eff = n_eff
        self.n_eff_encuesta = n_eff_encuesta
        self.usar_encuesta = usar_encuesta
        self.excluir = excluir_gala
        self.hasta = hasta_gala        # solo observaciones ANTERIORES a esta gala

        galas = [g for g in cfg["galas"]]
        fechas = [g["fecha"] for g in galas] + [FECHA_GALA28]
        self.fechas = fechas
        self.T = len(fechas)
        self.dt = np.array([max((_d(fechas[t + 1]) - _d(fechas[t])).days, 1) / 7.0
                            for t in range(self.T - 1)])

        nombres = {n for g in galas for n in g["placa"]}
        nombres |= set(cfg["placa_vigente"]["integrantes"])
        nombres |= set(cfg["encuesta_gala28"]["placa"])
        self.jug = sorted(nombres)
        self.idx = {n: i for i, n in enumerate(self.jug)}
        self.K = len(self.jug)

        self.obs = []
        for t, g in enumerate(galas):
            if self.excluir is not None and g["gala"] == self.excluir:
                continue
            if self.hasta is not None and g["gala"] >= self.hasta:
                continue
            self.obs.extend(self._obs_gala(g, t))
        if usar_encuesta and self.hasta is None:
            self.obs.extend(self._obs_encuesta(self.T - 1))

    # -- construccion de observaciones ---------------------------------------
    def _obs_gala(self, g, t):
        placa = [self.idx[n] for n in g["placa"]]
        sal = {self.idx[k]: v / 100.0 for k, v in g["salvados_cuota"].items()}
        vs = {self.idx[k]: v / 100.0 for k, v in g.get("versus", {}).items()}
        out = []
        if g["completa"] and vs:
            resto = 1.0 - sum(sal.values())
            q = {}
            q.update(sal)
            for k, v in vs.items():
                q[k] = v * resto
            vec = np.array([q.get(i, 0.0) for i in placa])
            vec = np.clip(vec, 1e-7, None); vec /= vec.sum()
            out.append(("multi", t, placa, vec, self.n_eff, g["gala"]))
        else:
            if sal:
                con = list(sal.keys())
                des = [i for i in placa if i not in sal]
                qc = np.array([sal[i] for i in con])
                out.append(("parcial", t, (placa, con, des), (qc, max(1 - qc.sum(), 1e-7)),
                            self.n_eff, g["gala"]))
            if len(vs) == 2:
                (a, pa), (b, pb) = list(vs.items())
                out.append(("par", t, (a, b), pa / (pa + pb), self.n_eff, g["gala"]))
        return out

    def _obs_encuesta(self, t):
        e = self.cfg["encuesta_gala28"]
        placa = [self.idx[n] for n in e["placa"]]
        con = [self.idx[k] for k in e["cuota"]]
        qc = np.array([v / 100.0 for v in e["cuota"].values()])
        des = [i for i in placa if i not in con]
        return [("parcial", t, (placa, con, des), (qc, max(1 - qc.sum(), 1e-7)),
                 self.n_eff_encuesta, "encuesta")]

    # -- verosimilitud + gradiente -------------------------------------------
    def nll_grad(self, x):
        TH = x.reshape(self.T, self.K)
        G = np.zeros_like(TH)
        f = 0.0
        for kind, t, a, q, w, _ in self.obs:
            th = TH[t]
            if kind == "multi":
                sub = th[a]
                m = sub.max()
                ex = np.exp(sub - m)
                Z = ex.sum()
                p = ex / Z
                f -= w * float(np.dot(q, sub - (m + math.log(Z))))
                G[t, a] -= w * (q - p)
            elif kind == "parcial":
                placa, con, des = a
                qc, qr = q
                sub = th[placa]
                m = sub.max()
                ex = np.exp(sub - m); Z = ex.sum(); p = ex / Z
                lZ = m + math.log(Z)
                if des:
                    sd = th[des]; md = sd.max()
                    exd = np.exp(sd - md); Zd = exd.sum()
                    lD = md + math.log(Zd)
                    pD = exd / Zd
                else:
                    lD, pD = -50.0, None
                f -= w * (float(np.dot(qc, th[con])) + qr * lD - lZ)
                G[t, placa] += w * p
                G[t, con] -= w * qc
                if des and pD is not None:
                    G[t, des] -= w * qr * pD
            else:
                i, j = a
                pa = q
                mx = max(th[i], th[j])
                ei, ej = math.exp(th[i] - mx), math.exp(th[j] - mx)
                Z = ei + ej
                si, sj = ei / Z, ej / Z
                f -= w * (pa * th[i] + (1 - pa) * th[j] - (mx + math.log(Z)))
                G[t, i] -= w * (pa - si)
                G[t, j] -= w * ((1 - pa) - sj)

        # prior de estado inicial
        f += float(np.dot(TH[0], TH[0])) / (2 * self.sigma0 ** 2)
        G[0] += TH[0] / self.sigma0 ** 2
        # random walk
        for t in range(self.T - 1):
            d = TH[t + 1] - TH[t]
            v = self.sigma ** 2 * self.dt[t]
            f += float(np.dot(d, d)) / (2 * v)
            G[t + 1] += d / v
            G[t] -= d / v
        return f, G.ravel()

    def ajustar(self):
        x0 = np.zeros(self.T * self.K)
        r = minimize(self.nll_grad, x0, jac=True, method="L-BFGS-B",
                     options={"maxiter": 20000, "maxfun": 40000,
                              "ftol": 1e-15, "gtol": 1e-10})
        # La verosimilitud es invariante a sumar una constante por corte; el prior
        # (ridge sobre el estado inicial + random walk) fija esa constante en 0,
        # asi que NO se centra a posteriori: hacerlo desplazaria a los jugadores
        # sin observaciones (Charlotte, Pincoya) por un artefacto de normalizacion.
        self.TH = r.x.reshape(self.T, self.K)
        self.res = r
        return self.TH

    # -- log-verosimilitud de una gala bajo el ajuste (para CV) --------------
    def loglik_gala(self, g):
        t = [i for i, gg in enumerate(self.cfg["galas"]) if gg["gala"] == g["gala"]][0]
        th = self.TH[t]
        tot = 0.0
        for kind, _, a, q, w, _ in self._obs_gala(g, t):
            if kind == "multi":
                sub = th[a]; m = sub.max(); ex = np.exp(sub - m); Z = ex.sum()
                tot += float(np.dot(q, sub - (m + math.log(Z))))
            elif kind == "parcial":
                placa, con, des = a
                qc, qr = q
                sub = th[placa]; m = sub.max(); Z = np.exp(sub - m).sum()
                lZ = m + math.log(Z)
                if des:
                    sd = th[des]; md = sd.max(); lD = md + math.log(np.exp(sd - md).sum())
                else:
                    lD = -50.0
                tot += float(np.dot(qc, th[con])) + qr * lD - lZ
            else:
                i, j = a; pa = q
                mx = max(th[i], th[j]); Z = math.exp(th[i] - mx) + math.exp(th[j] - mx)
                tot += pa * th[i] + (1 - pa) * th[j] - (mx + math.log(Z))
        return tot


# ---------------------------------------------------------------------------

def cv_una_afuera(cfg, sigmas, **kw):
    """Interpolacion: deja una gala afuera y la reconstruye desde sus vecinas."""
    filas = []
    for s in sigmas:
        tot = 0.0
        for g in cfg["galas"]:
            m = ModeloDinamico(cfg, sigma=s, excluir_gala=g["gala"], **kw)
            m.ajustar()
            tot += m.loglik_gala(g)
        filas.append((s, tot))
    return filas


def cv_un_paso(cfg, sigmas, desde=20, **kw):
    """
    Validacion cruzada UN PASO ADELANTE: para cada gala t, se ajusta el modelo
    SOLO con las galas anteriores (y sin la encuesta) y se evalua la
    verosimilitud de la gala t bajo el estado propagado. Es exactamente la tarea
    del modelo -- predecir la proxima gala -- y a diferencia de la version
    "una afuera" no se puede ganar loglik dejando que sigma tienda a infinito.
    """
    galas = cfg["galas"]
    filas = []
    for s in sigmas:
        tot, n = 0.0, 0
        for g in galas:
            if g["gala"] < desde:
                continue
            m = ModeloDinamico(cfg, sigma=s, hasta_gala=g["gala"],
                               usar_encuesta=False, **kw)
            m.ajustar()
            tot += m.loglik_gala(g)
            n += 1
        filas.append((s, tot, n))
    return filas


def covarianza_final(m: ModeloDinamico, eps=1e-3):
    """Laplace sobre el ultimo corte temporal, condicionando el resto en su modo."""
    x = m.TH.ravel().copy()
    K, T = m.K, m.T
    base = (T - 1) * K
    H = np.zeros((K, K))
    for i in range(K):
        xp = x.copy(); xp[base + i] += eps
        xm = x.copy(); xm[base + i] -= eps
        _, gp = m.nll_grad(xp)
        _, gm = m.nll_grad(xm)
        H[i] = (gp[base:base + K] - gm[base:base + K]) / (2 * eps)
    H = 0.5 * (H + H.T)
    cov = np.linalg.pinv(H)
    P = np.eye(K) - np.ones((K, K)) / K
    return P @ cov @ P.T


if __name__ == "__main__":
    cfg = cargar()
    print("### Validacion cruzada leave-one-gala-out para la deriva semanal sigma")
    filas = cv_sigma(cfg, [0.25, 0.5, 0.75, 1.0, 1.3, 1.7, 2.2, 3.0])
    for s, ll in filas:
        print(f"  sigma={s:<5} loglik_cv={ll:>10.3f}")
    mejor = max(filas, key=lambda z: z[1])[0]
    print(f"\n  -> sigma optimo = {mejor}")

    m = ModeloDinamico(cfg, sigma=mejor)
    TH = m.ajustar()
    vig = cfg["placa_vigente"]["integrantes"] + cfg["placa_vigente"]["libres"]
    print("\n### Trayectoria del rechazo latente theta (por gala)")
    hdr = "jugador".ljust(11) + "".join(f"G{g['gala']:>5}" for g in cfg["galas"]) + f"{'HOY':>7}"
    print(hdr)
    for n in sorted(vig, key=lambda n: -TH[-1, m.idx[n]]):
        fila = "".join(f"{TH[t, m.idx[n]]:>6.2f}" for t in range(m.T))
        print(f"{n:<11}{fila}")

    print("\n### Prediccion gala 28 (10/08) - probabilidad de ELIMINACION")
    placa = [m.idx[n] for n in cfg["placa_vigente"]["integrantes"]]
    th = TH[-1, placa]
    p = np.exp(th - th.max()); p /= p.sum()
    for n, pi in sorted(zip(cfg["placa_vigente"]["integrantes"], p), key=lambda z: -z[1]):
        print(f"   {n:<12}{100*pi:>7.1f}%")

    print("\n### Ajuste: observado vs predicho en las galas completas")
    err = []
    for t, g in enumerate(cfg["galas"]):
        if not g["completa"]:
            continue
        th = TH[t, [m.idx[n] for n in g["placa"]]]
        p = np.exp(th - th.max()); p /= p.sum()
        resto = 1 - sum(g["salvados_cuota"].values()) / 100
        obs = {k: v / 100 for k, v in g["salvados_cuota"].items()}
        for k, v in g["versus"].items():
            obs[k] = v / 100 * resto
        for n, pi in zip(g["placa"], p):
            err.append(abs(obs.get(n, 0) - pi))
        top_obs = max(obs, key=obs.get)
        top_pred = g["placa"][int(np.argmax(p))]
        print(f"  G{g['gala']}: eliminado real={g['eliminado']:<11} "
              f"mas votado predicho={top_pred:<11} {'OK' if top_pred == g['eliminado'] else 'X'}")
    print(f"\n  error absoluto medio por celda: {100*np.mean(err):.2f} puntos porcentuales")
