#!/usr/bin/env python3
"""Atualiza os apps da loja para a release estável mais recente de cada projeto.

Para cada app: lê a última release no GitHub, confere se a imagem já existe no
GHCR, pega o digest e reescreve a imagem no docker-compose.yml e a versão no
umbrel-app.yml. O Umbrel compara a versão do manifesto e oferece a atualização.

Uso:
  python3 scripts/atualizar_apps.py            # aplica as mudanças
  python3 scripts/atualizar_apps.py --simular  # só mostra o que faria

Só usa a biblioteca padrão. GITHUB_TOKEN (opcional) evita o limite da API.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# tag: como a tag da imagem no GHCR se forma a partir da versão (sem o "v")
APPS = [
    {
        "app": "extras-shelfmark",
        "repo": "calibrain/shelfmark",
        "imagem": "ghcr.io/calibrain/shelfmark",
        "tag": "v{versao}",
    },
    {
        "app": "extras-dispatcharr",
        "repo": "Dispatcharr/Dispatcharr",
        "imagem": "ghcr.io/dispatcharr/dispatcharr",
        "tag": "{versao}",
    },
]

ACCEPT_INDICE = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def pedir(url, headers=None, metodo="GET"):
    req = urllib.request.Request(url, headers=headers or {}, method=metodo)
    req.add_header("User-Agent", "umbrel-loja-atualizador")
    return urllib.request.urlopen(req, timeout=30)


def ultima_release(repo):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with pedir(f"https://api.github.com/repos/{repo}/releases/latest", headers) as r:
        return json.load(r)["tag_name"]


def digest_ghcr(imagem, tag):
    nome = imagem.removeprefix("ghcr.io/")
    with pedir(f"https://ghcr.io/token?scope=repository:{nome}:pull") as r:
        token = json.load(r)["token"]
    headers = {"Authorization": f"Bearer {token}", "Accept": ACCEPT_INDICE}
    try:
        with pedir(f"https://ghcr.io/v2/{nome}/manifests/{tag}", headers, "HEAD") as r:
            return r.headers["Docker-Content-Digest"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def como_tupla(versao):
    return tuple(int(p) for p in versao.split("."))


def atualizar(cfg, simular):
    pasta = RAIZ / cfg["app"]
    manifesto = pasta / "umbrel-app.yml"
    compose = pasta / "docker-compose.yml"
    texto_m = manifesto.read_text(encoding="utf-8")
    texto_c = compose.read_text(encoding="utf-8")

    atual = re.search(r'^version: "([^"]+)"$', texto_m, re.M).group(1)
    tag_release = ultima_release(cfg["repo"])
    nova = tag_release.removeprefix("v")

    if not SEMVER.match(nova):
        print(f"{cfg['app']}: release {tag_release} fora do padrão X.Y.Z, ignorada")
        return None
    if como_tupla(nova) <= como_tupla(atual):
        print(f"{cfg['app']}: já está na {atual}")
        return None

    tag_imagem = cfg["tag"].format(versao=nova)
    digest = digest_ghcr(cfg["imagem"], tag_imagem)
    if not digest:
        print(f"{cfg['app']}: {nova} saiu, mas a imagem {tag_imagem} ainda não está no GHCR")
        return None

    padrao = re.compile(
        rf"^(\s*image:\s*){re.escape(cfg['imagem'])}:[^@\s]+@sha256:[0-9a-f]{{64}}\s*$", re.M
    )
    novo_c, n = padrao.subn(rf"\g<1>{cfg['imagem']}:{tag_imagem}@{digest}", texto_c)
    if n != 1:
        raise SystemExit(f"{cfg['app']}: esperava 1 linha de imagem no compose, achei {n}")

    novo_m = texto_m.replace(f'version: "{atual}"', f'version: "{nova}"', 1)
    # Links do ícone e das notas apontam para a tag da release (vX.Y.Z)
    novo_m = novo_m.replace(f"v{atual}", f"v{nova}")

    print(f"{cfg['app']}: {atual} -> {nova} ({tag_imagem}@{digest[:19]}…)")
    if not simular:
        compose.write_text(novo_c, encoding="utf-8")
        manifesto.write_text(novo_m, encoding="utf-8")
    return f"{cfg['app'].removeprefix('extras-')} {nova}"


def main():
    simular = "--simular" in sys.argv
    mudancas = [m for cfg in APPS if (m := atualizar(cfg, simular))]

    saida = os.environ.get("GITHUB_OUTPUT")
    if saida:
        with open(saida, "a", encoding="utf-8") as f:
            f.write(f"mudou={'true' if mudancas else 'false'}\n")
            f.write(f"mensagem=Atualiza {', '.join(mudancas)}\n")


if __name__ == "__main__":
    main()
