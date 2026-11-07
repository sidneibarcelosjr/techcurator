# TechCurator

Sistema web de curadoria de notícias de tecnologia que estima **indícios de credibilidade** a partir do **consenso entre múltiplas fontes** e de **sinais textuais**, sem depender de rótulos de veracidade.

Este repositório é o código-fonte do Trabalho de Conclusão de Curso:

> **Estimativa de indícios de credibilidade em notícias de tecnologia por consenso entre múltiplas fontes e sinais textuais**
> Sidnei Barcelos Junior. Bacharelado em Sistemas de Informação, Instituto Federal Catarinense, Câmpus Araquari, 2026.
> Orientador: Prof. Dr. Mehran Misaghi.


## Importante: o que o sistema faz (e o que não faz)

O selo de credibilidade (alta, média, baixa) é um **indício**, não um veredito de verdadeiro ou falso. Ele combina:

1. **Consenso entre fontes**: notícias que tratam do mesmo fato são agrupadas (TF-IDF, similaridade de cosseno e janela temporal) e a cobertura é o número de fontes distintas no grupo.
2. **Sinais textuais**: clickbait, linguagem sensacionalista, conteúdo promocional e ausência de atribuição de fontes.

A identidade ou reputação da fonte **não** entra no cálculo (evita raciocínio circular).

## Funcionalidades

- Coleta periódica via RSS de portais brasileiros de tecnologia
- Pipeline de PLN: relevância temática, limpeza, palavras-chave e deduplicação
- Agrupamento de notícias por fato e cálculo da cobertura entre fontes
- Estimativa de credibilidade com selo no feed e no detalhe da notícia
- Comandos de avaliação usados nos experimentos da monografia

## Arquitetura

Seis serviços orquestrados com Docker Compose:

| Serviço | Tecnologia | Papel |
|---|---|---|
| `backend` | Django 5 + Django REST Framework | API REST, pipeline de PLN, coleta |
| `frontend` | React 18 + Vite | Interface web (SPA) |
| `db` | PostgreSQL 16 | Armazenamento |
| `redis` | Redis 7 | Broker de tarefas |
| `celery` | Celery 5 | Execução assíncrona |
| `celery-beat` | django-celery-beat | Agendamento periódico |

## Como executar

**Requisitos:** Docker e Docker Compose (no macOS/Windows, Docker Desktop aberto).

```bash
# 1. Clonar
git clone https://github.com/sidneibarcelosjr/techcurator.git
cd techcurator

# 2. Configurar variáveis de ambiente
cp backend/.env.example .env      # ajuste os valores (SECRET_KEY, senha do banco)

# 3. Subir os serviços (as migrations rodam automaticamente)
docker compose up -d --build

# 4. Coletar notícias (primeira vez)
docker compose exec backend python manage.py run_scraping

# 5. Agrupar e calcular credibilidade
docker compose exec backend python manage.py run_clustering --persist
```

Acesse o sistema em **http://localhost:5173** (API em http://localhost:8000).

> **macOS/Linux:** se o backend não subir com `permission denied`, rode `chmod +x backend/entrypoint.sh`.
> **Segurança:** o arquivo `.env` nunca é versionado. Defina uma `SECRET_KEY` própria.

## Reproduzindo os experimentos

Comandos usados no Capítulo 5 da monografia:

```bash
# Exportar amostra para anotação do gabarito (um dia, ~150 notícias)
docker compose exec backend python manage.py export_gabarito --de AAAA-MM-DD --ate AAAA-MM-DD --amostra 150

# PP1: ARI e V-measure por limiar, contra o gabarito anotado
docker compose exec backend python manage.py avaliar_clustering --gabarito gabarito.xlsx

# Diagnóstico: onde o agrupamento diverge do gabarito
docker compose exec backend python manage.py diagnostico_clustering --gabarito gabarito.xlsx --limiar 0.50

# PP2: Spearman e Mann-Whitney (qualidade textual x cobertura)
docker compose exec backend python manage.py analisar_pp2
```

Os resultados completos estão no Capítulo 5 da monografia.

**Sobre os dados:** a base coletada contém conteúdo de portais de terceiros e **não é distribuída** neste repositório. O processo de coleta é reproduzível com `run_scraping`; os resultados variam conforme o período coletado.

## Estrutura do projeto

```
backend/
  apps/
    accounts/    autenticação (JWT)
    news/        modelos (Article, Source, Cluster) e API
    nlp/         pipeline, classificador, clusterer, credibilidade
    scraping/    coletores (spiders) e orquestração
  curadoria/     configurações do Django e do Celery
frontend/
  src/           componentes, páginas e serviços (React)
docker-compose.yml
```

## Limitações

Anotação do conjunto de referência por avaliador único; base de sete dias; o sistema produz indícios e não mede veracidade. Detalhes no Capítulo 5 da monografia.

## Licença

Distribuído sob a licença MIT. Veja o arquivo `LICENSE`.
