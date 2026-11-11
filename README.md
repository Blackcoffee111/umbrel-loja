# Loja "Extras" para umbrelOS

Loja da comunidade do Umbrel com apps que não estão na loja oficial.

| App | Versão | Porta | Observação |
|---|---|---|---|
| Shelfmark (`extras-shelfmark`) | 1.6.2 | 8097 | Busca e baixa livros. Precisa do Calibre-Web Automated (loja oficial) |
| Dispatcharr (`extras-dispatcharr`) | 0.33.0 | 9191 | IPTV, EPG e canais. Links abertos sem o login do Umbrel; a interface tem login próprio |

## Como adicionar ao Umbrel

1. App Store → menu `⋯` no canto superior direito → **Community App Stores**.
2. Cole a URL deste repositório e clique em **Add**.
3. Abra a **Extras App Store** e instale o app.

## Atualizações

A Action [`atualizar-apps.yml`](.github/workflows/atualizar-apps.yml) roda todo dia
às 05:17 UTC (e sob demanda em Actions → Atualizar apps → Run workflow). Ela
procura a última release estável de cada projeto, confere se a imagem já está no
GHCR, fixa a nova tag com o digest e faz o commit. O Umbrel lê a loja a cada
5 minutos e mostra **Update** no app.

Para testar localmente sem mudar nada:

```bash
python3 scripts/atualizar_apps.py --simular
```

Para incluir outro app, acrescente uma entrada em `APPS` no
[`scripts/atualizar_apps.py`](scripts/atualizar_apps.py).

## Pastas

### Shelfmark

| No container | No Umbrel | Para quê |
|---|---|---|
| `/config` | `app-data/extras-shelfmark/data/config` | Configuração do Shelfmark |
| `/books` | `app-data/calibre-web-automated/data/book-ingest` | Entrada do CWA (importação automática). Configurável no painel em "Destino dos livros" |
| `/downloads` | `home/Downloads` | Mesma pasta e mesmo caminho do Transmission |

### Dispatcharr

| No container | No Umbrel | Para quê |
|---|---|---|
| `/data` | `app-data/extras-dispatcharr/data` | Banco (Postgres), chave secreta (`jwt`), logos, plugins, gravações e backups |

O fuso horário (`TZ`) é configurado no painel do Umbrel, nas variáveis do app.
