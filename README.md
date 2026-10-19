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


# Documentação Detalhada

## 1. Introdução

## 2. Indexação Geohash

## 3. Árvore Trie

## 4. Simulador de Geração de Entregadores

A modulo `src/simulador.py` contém a geração e a correção das posições dos entregadores, distribuindo os entregadores equitativamente entre os restaurantes por meio de uma distrbuição normal centrada em cada um dos restaurantes.

### 4.1 Distribuição Espacial Baseada em Demanda

A função `gerar_entregadores_normais` é responsável pela geração da posição inicial dos entregadores. Dado N sendo o Número de Entregadores a serem gerados e M o número de restaurante, a geração é feita da seguinte forma:

- lê a geometria de cada bar e usa suas coordenadas $x$, $y$, projetadas em metros como centro da distribuição normal.
- A quantidade solicitada é dividida entre os bares: todos recebem a mesma inteira quantidade $E$, obtida através de \(\lfloor N/M \rfloor\), e o resto R, caso a divisão não seja inteira, é distribuído aleatoriamente entre alguns bares. 
- Para cada posição, são geradas coordenadas $x$ e $y$ com o desvio padrão configurado, que por padrão é 400 metros, a fim de não serem gerados varios entregadores no mesmo ponto.

Cada entregador recebe um id, o nome do bar de origem, as coordenadas matemáticas em metros ('EPSG:31983') e sua conversão para latitude e longitude ('EPSG:4326').

Como o exemplo a seguir mostra, essa geração ainda não é a ideal, uma vez que nem todos os pontos gerados respeitam a malha viária, como no exemplo a seguir, os pontos circulados foram plotados fora das ruas da malha, inclusive dentro do Parque Municipal Américo Renné.

![alt text](assets/images/frota_mat.png)

Inicialmente, essa função realizava a geração tendo graus como base de medida (latitude e longitude), porém, essa medida é menos intuitiva, uma vez que o desvio padrão também deveria ser na mesma medida, onde 0.001 graus de desvio padrão significava cerca de 1km em cada direção, tornando o entendimento menos direto.

### 4.2 Restrição Viária (Realismo Geográfico)

Como mencionado, a geração acima é feita com base em uma distribuição normal matemática, fatalmente haverá entregadores com coordenadas irreais, e.g. no meio da Lagoa da Pampulha, em cima de telhados, etc. Por isso, foi criada a função `corrigir_para_ruas`, que aloca os entregadores para posições válidas dentro de ruas reais.

A função `corrigir_para_ruas` recebe a tabela com os entregadores e suas posições matemáticas e, para cada entregador, consulta a aresta da malha viária de BH mais próxima de cada posição matemática com o OSMnx. Em seguida, projeta o ponto com coordenadas $x$ e $y$ em metros na rua usando o Shapely e transforma as coordenadas resultantes para latitude e longitude. Dessa forma, a posição corrigida pode ser exibida sobre a malha viária.

Para encaixar os entregadores sobre a linha real das ruas, a função chama `nearest_edges` do osmnx, que identifica o trecho de rua mais próximo de cada ponto matemático. A partir daí, é extraída a geometria da rua. Utilizando o Shapely, o ponto é projetado sobre essa linha: o método `project` descobre a posição exata ao longo do trecho e o `interpolate` pega as novas coordenadas. Como toda essa operação ocorre em metros `EPSG:31983`, as distâncias e projeções são tratadas em metros. Por fim, as coordenadas corrigidas são convertidas para graus (latitude e longitude `EPSG:4326`) para a renderização no mapa da interface.

A seguir, temos um exemplo da geração com a correção aplicada, onde todos os entregadores são plotados dentro das ruas.

![alt text](assets/images/frota_rua.png)

O simulador, além de utilizado na interface, pode ser executado pelo terminal. Nesse modo, ele solicita a quantidade de entregadores e grava os CSVs matemáticos e corrigidos nos caminhos padrão definidos em `utilities/constants.py`.

## 5. Interface do mapa

O módulo `utilities/interface.py` prepara os dados para o gráfico Plotly. Os bares são exibidos em azul; os entregadores são coloridos conforme o campo `filtrado` (vermelho para `True`, cinza para `False`). A função também define o centro e o nível inicial de zoom do mapa.

## 6. Aplicação web 

O arquivo `app.py` monta a aplicação Dash. Na abertura, carrega os bares e apresenta o mapa inicial, a princípior sem os entregadores. A página possui um campo para inserir a quantidade de entregadores a serem gerados, um botão para a geração e uma opção para salvar os resultados em CSV.

Ao clicar no botão, o callback valida a quantidade de entregadores, onde é necessário que o valor inserido se inteiro maior que zero, gera uma nova frota, carrega a malha, corrige as posições para as ruas e atualiza o mapa. A frota de entregadores que foi gerada a esse ponto substitui a que estava sendo exibida anteriormente.

A página também possui um checkbox **Salvar CSVs desta geração**, quando este esta marcado, o app grava dois arquivos: um com as posições matemáticas e outro com as posições corrigidas. Os nomes recebem um identificador de data e hora e um código aleatorio, a fim de evitar a sobrescrição dos arquivos gerados anteriormente.

## INTEGRANTES

- Marney Santos de Melo — 2024106034
- Rafael Resende Miranda — 2024065990
- Victor Murilo Kaizer — 2024096551