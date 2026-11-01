#!/usr/bin/env python3
"""
Fonte única das skills de agente (ADR 2026-05-13: a SKILL.md vive no repo do agente).

O marketplace guarda um ESPELHO em plugins/<agente>/skills/<agente>/SKILL.md. Este script
compara cada espelho com o canônico (SKILL.md na raiz do repo Sementesmana/<agente>, branch
main) e classifica:

  igual          nada a fazer
  sem-canonico   o repo não tem SKILL.md na raiz: o espelho é a única versão (migrar um dia)
  atrasado       todo o conteúdo do espelho já está no canônico -> seguro copiar (--aplicar)
  conflito       o espelho tem linhas que o canônico NÃO tem -> alguém editou o espelho;
                 precisa de merge humano. NUNCA é copiado por cima (as duas cópias já
                 divergiram em direções opostas antes — memória reference_skill_canonico_x_espelho)

Uso:
  GITHUB_TOKEN=... python3 _tools/sincronizar_espelhos.py            # só relatório
  GITHUB_TOKEN=... python3 _tools/sincronizar_espelhos.py --aplicar [agente ...]
      # copia os "atrasado" (todos, ou só os agentes listados) e sobe o patch da versão
Regra para quem mantém: edite SEMPRE o SKILL.md no repo do agente; depois rode este script.
"""
import json, os, re, sys, urllib.request, urllib.error

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORG = "Sementesmana"


def canonico(repo, token):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{ORG}/{repo}/contents/SKILL.md",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.raw"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def norm(t):
    return t.replace("\r\n", "\n").rstrip("\x00").rstrip() + "\n"


def bump(v):
    a, b, c = (v.split(".") + ["0", "0"])[:3]
    return f"{a}.{b}.{int(c) + 1}"


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        sys.exit("defina GITHUB_TOKEN (leitura dos repos da org)")
    aplicar = "--aplicar" in sys.argv
    so = {a for a in sys.argv[1:] if not a.startswith("--")}
    mkt_p = os.path.join(RAIZ, ".claude-plugin", "marketplace.json")
    mkt = json.load(open(mkt_p, encoding="utf-8"))
    res = {}
    for nome in sorted(os.listdir(os.path.join(RAIZ, "plugins"))):
        esp_p = os.path.join(RAIZ, "plugins", nome, "skills", nome, "SKILL.md")
        if nome == "mana-skills" or not os.path.isfile(esp_p):
            continue
        esp = norm(open(esp_p, encoding="utf-8").read())
        can = canonico(nome, token)
        if can is None:
            st = "sem-canonico"
        else:
            can = norm(can)
            if can == esp:
                st = "igual"
            else:
                linhas_can = set(can.splitlines())
                so_no_espelho = [l for l in esp.splitlines() if l.strip() and l not in linhas_can]
                st = "conflito" if so_no_espelho else "atrasado"
        res.setdefault(st, []).append(nome)
        if aplicar and st == "atrasado" and (not so or nome in so):
            open(esp_p, "w", encoding="utf-8", newline="\n").write(can)
            for x in mkt["plugins"]:
                if x["name"] == nome:
                    x["version"] = bump(x["version"])
                    pj = os.path.join(RAIZ, "plugins", nome, ".claude-plugin", "plugin.json")
                    j = json.load(open(pj, encoding="utf-8")); j["version"] = x["version"]
                    open(pj, "w", encoding="utf-8").write(json.dumps(j, ensure_ascii=False, indent=2) + "\n")
    if aplicar:
        open(mkt_p, "w", encoding="utf-8").write(json.dumps(mkt, ensure_ascii=False, indent=2) + "\n")
    for st in ("igual", "atrasado", "conflito", "sem-canonico"):
        print(f"{st:13} {len(res.get(st, [])):3}  {', '.join(res.get(st, []))}")
    if aplicar:
        print("\n'atrasado' copiados do canônico. 'conflito' exige merge humano.")


if __name__ == "__main__":
    main()
