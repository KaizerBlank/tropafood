# Tropafood

TP1 ALG II

## Funcionalidades

- Exibe os bares cadastrados em `data/bares.csv`.
- Permite informar o numero N de entregadores que serao gerados
- Distribui os N entregadores equitativamente entre os bares com base numa distribuição normal centrada em cada bar. O resto da divisão é distribuído entre alguns bares aleatoriamente.
- Para nao gerar todos os entregadores no mesmo ponto, gera posições ao redor dos bares usando uma distribuição normal com desvio padrão de 400 metros.
- Ajusta cada posição para algum ponto da aresta (rua) mais proxima usando a malha viária do OpenStreetMap, via OSMnx.
- Permite salvar os resultados em CSV pela opção **Salvar CSVs desta geração**.

## Requisitos

- Docker Desktop instalado e em execução.
- Acesso à internet na primeira geração, caso a malha viária ainda não esteja armazenada localmente.

## Executar a interface

Na pasta raiz do projeto, construa a imagem:

```powershell
docker build -t tropafood-app -f dockerfile .
```

Inicie o app com os arquivos locais montados no container:

```powershell
docker run --rm -p 8050:8050 -v "${PWD}:/app" tropafood-app
```

Abra [http://localhost:8050](http://localhost:8050) no navegador. O volume `-v` permite que o container use os arquivos do projeto no computador.

Na página, informe uma quantidade inteira positiva e clique em **Gerar entregadores**. A cada geração, o conjunto exibido é substituído pelo novo conjunto.

### Salvar os resultados

Marque **Salvar CSVs desta geração** antes de gerar. O app grava dois arquivos na pasta `data/`:

- `entregadores_matematicos_<identificador>.csv`: posições obtidas pela distribuição normal, antes do ajuste para as ruas.
- `entregadores_corrigidos_<identificador>.csv`: posições após o ajuste para a malha viária.

O identificador conta com data, hora (configurados no conteiner) e um código único. Assim, cada geração cria novos arquivos e não sobrescreve os CSVs anteriores. Se a opção estiver desmarcada, os CSVs não serão salvos.

## Executar o simulador pelo terminal

O simulador pode ser executado sem iniciar a interface:

```powershell
docker run --rm -it -v "${PWD}:/app" tropafood-app python -m src.simulador
```

O programa solicita a quantidade de entregadores. Se a resposta ficar vazia, usa 500. O arquivo de bares e o desvio padrão são definidos em `utilities/constants.py`.

No modo terminal, os arquivos são gravados nos caminhos fixos `data/entregadores_matematicos.csv` e `data/entregadores_corrigidos.csv`; execuçõe posteriores sobrescrevem os arquivos existentes.

## Malha viária

Na primeira geração, `src/grafo.py` baixa a malha viaria de Belo Horizonte, converte para metros (`EPSG:31983`) e salva uma cópia em `data/malha_bh_drive_31983.graphml`. Nas execuções seguintes, reutiliza o arquivo ja gerado

## Geocodificador

O script `scripts/geocodificador.py` busca coordenadas para os endereços de `data/bares.csv` e grava o resultado em `data/bares_com_coordenadas.csv`. Ele consulta o OpenStreetMap endereço por endereço e inclui uma pausa entre as consultas, pode levar horas para terminar

## Configurações

`utilities/constants.py` centraliza os caminhos, o desvio padrão e os sistemas de coordenadas usados pelo app e pelo simulador. O arquivo de entrada padrão é `data/bares.csv`, e o desvio padrão é 400 metros.

## Estrutura do projeto

```text
tropafood/
├── app.py                       # Interface interativa em Dash
├── assets/style.css             # Estilos da interface
├── data/                        # Bases, resultados e cache local do grafo
├── docs/tp1.pdf                 # Enunciado do trabalho
├── entities/                    # Entidades de restaurantes e entregadores
├── scripts/geocodificador.py    # Geocodificação de endereços
├── src/
│   ├── grafo.py                 # Carregamento ou geração da malha viária
│   ├── simulador.py             # Geração e ajuste das posições
│   ├── geohash.py               # Estrutura de geohash
│   └── trie.py                  # Estrutura Trie
├── utilities/
│   ├── constants.py             # Configurações compartilhadas
│   ├── files.py                 # Leitura de dados
│   └── interface.py             # Preparação do mapa
├── dockerfile                  
├── main.py                      
└── requirements.txt             
```

`src/geohash.py` e `src/trie.py` documenta aqui @raiz

## INTEGRANTES

- Marney Santos de Melo — 2024106034
- Rafael Resende Miranda — 2024065990
- Victor Murilo Kaizer — 2024096551