# Painel Financeiro

[![CI](https://github.com/WallaksCardoso/painel-financeiro/actions/workflows/ci.yml/badge.svg)](https://github.com/WallaksCardoso/painel-financeiro/actions/workflows/ci.yml)

Meu painel de fluxo de caixa. Mostra quanto sobra em cada mês com o que já está comprometido
hoje (contas fixas, faturas de cartão, parcelas e dívidas) e quando cada parcela termina. Fiz para
substituir a planilha que eu atualizava à mão todo mês.

![Fluxo de caixa](docs/img/fluxo.jpg)

| Visão do mês | Cartões |
| --- | --- |
| ![Mês](docs/img/mes.jpg) | ![Cartões](docs/img/cartoes.jpg) |

![Dashboard](docs/img/dashboard.jpg)

> Os prints usam os dados fictícios do comando de demonstração (veja abaixo).

## O que tem

O fluxo de caixa mês a mês (entradas, contas, quitações, investimentos e fatura, com sobra e
acumulado), a visão de um mês com o plano e a meta, os cartões com a fatura de cada um, as
transações (mensais, eventuais e parceladas), dívidas, reserva de emergência e orçamento por
categoria. Categorias, meios de pagamento e os demais valores se editam pela tela, e dá para
exportar tudo em JSON.

## Regras que deram trabalho

- Fatura pelo fechamento, caixa pelo vencimento. A compra entra na fatura do mês em que ela fecha,
  mas no fluxo de caixa a fatura conta no mês em que vence, mesmo quando o vencimento cai no mês
  seguinte ao fechamento.
- Dinheiro em centavos. As parcelas são divididas em centavos e a sobra vai para as últimas
  (R$ 100 em 3x = 33,33 + 33,33 + 33,34).
- Recorrências. Um lançamento mensal gera a previsão dos meses seguintes, e o dia habitual é deduzido
  do histórico. Salário antecipado por causa de feriado (inclusive os móveis, calculados a partir da
  Páscoa) não vira o novo padrão, e a previsão já cai em dia útil.
- Cliques simultâneos não duplicam os recorrentes: a geração é idempotente e tem trava, com um teste
  que dispara requisições em paralelo.
- Uma quitação não passa do que falta da dívida, e a reserva não fica negativa em nenhuma data do
  histórico.

Backend em Python 3.12 com FastAPI, SQLAlchemy 2, Alembic e SQLite. Frontend em React 19 com
TypeScript, Vite, Tailwind CSS 4 e Recharts. Docker Compose com nginx na frente e GitHub Actions.

## Como rodar

### Com Docker (qualquer sistema)

```bash
docker compose up -d --build
docker compose exec backend python -m app.demo   # opcional: dados fictícios
```

Abra <http://localhost:8080>. Os dados ficam no volume `dados`.

### Em modo desenvolvimento

Backend (Python 3.11+):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m app.demo               # opcional: dados fictícios num banco vazio
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

Frontend (Node 20+), em outro terminal:

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173 (proxy de /api para a porta 8000)
```

No Windows, `iniciar.bat` sobe os dois de uma vez e `parar.bat` encerra.

O banco é um arquivo SQLite (`backend/painel.db`, ou o caminho em `PAINEL_DB`), criado e
atualizado na subida pelas migrações do Alembic. Para uma mudança de esquema:
`alembic revision --autogenerate -m "descrição"` dentro de `backend/`.

## Backup

O comando de backup copia o banco para uma pasta, com data e hora no nome
(`painel-2026-03-05-083000.db`), confere a integridade da cópia e mantém as 30 mais recentes. Pode
rodar com o painel aberto.

```bash
cd backend
python -m app.backup <pasta>             # ou defina PAINEL_BACKUP_DIR e omita a pasta
python -m app.backup <pasta> --manter 0  # guarda todas as cópias
```

No Windows, `backup.bat <pasta>` faz o mesmo. Para automatizar, defina a pasta uma vez (uma pasta
do Google Drive ou de outro serviço de nuvem tira a cópia da máquina) e abra um novo terminal:

```bat
setx PAINEL_BACKUP_DIR "G:\Meu Drive\Backups\painel-financeiro"
```

Com a variável definida, o `iniciar.bat` faz um backup antes de subir o painel. Para ter também uma
cópia diária mesmo sem abrir o painel, agende o `backup.bat` no Agendador de Tarefas:

```bat
schtasks /create /tn "Painel Financeiro - Backup" /sc daily /st 20:00 /tr "\"C:\caminho\do\painel-financeiro\backup.bat\""
```

Para restaurar, pare o painel (`parar.bat`) e coloque a cópia no lugar de `backend/painel.db`, com
esse nome; na próxima subida, as migrações atualizam o banco se ele for de uma versão antiga. No
Docker, o banco fica no volume `dados`:

```bash
docker compose cp backend:/data/painel.db ./painel-backup.db
```

O botão Exportar gera um JSON com todos os dados, bom para consulta ou para levar a outra
ferramenta, mas a restauração é pelo arquivo do banco.

## Qualidade

```bash
# backend
ruff check . && ruff format --check . && pytest

# frontend
npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
```

A CI roda tudo isso a cada push e monta as imagens Docker. Os testes do backend (pytest)
cobrem as regras de domínio (fatura, parcelas, recorrências, dia útil, dívidas, reserva e
orçamento) com um banco em memória por teste. No frontend, Vitest e Testing Library
testam formatação, datas, mensagens de erro e o comportamento de formulários.

## Commits

Mensagens no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/):
`feat:` (funcionalidade), `fix:` (correção), `refactor:`, `test:`, `docs:`, `style:`,
`build:` e `ci:`. Antes de enviar, rode as verificações da seção acima.

## Estrutura

```
backend/
  app/
    main.py          app FastAPI; cria/atualiza o banco na subida
    config.py        caminho do banco (PAINEL_DB) e CORS
    database.py      engine, sessão (Db) e aplicação das migrações na subida
    models.py        tabelas (SQLAlchemy)
    schemas.py       entrada e saída da API (Pydantic)
    services/        regras de negócio: fatura, projecao, recorrentes, mes, dividas…
    routers/         rotas HTTP
    demo.py          dados fictícios de demonstração
    backup.py        cópia do banco com data no nome (python -m app.backup)
  migrations/        migrações do banco (Alembic)
  tests/             um arquivo por assunto
frontend/
  src/
    pages/           Fluxo, Mes, Cartoes, Transacoes, Dashboard, Dividas, Reserva,
                     Orcamento, Configuracoes
    components/      layout, modais e formulários compartilhados
    contexts/        opções editáveis e mês selecionado
    hooks/ lib/      busca de dados, formatação, datas e rótulos
```

## Licença

[MIT](LICENSE)
