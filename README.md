# Tropafood

TP1 ALG II

## Funcionalidades

- Exibe os bares cadastrados em `data/bares.csv`.
- Permite informar o numero N de entregadores que serao gerados
- Distribui os N entregadores equitativamente entre os bares com base numa distribuição normal centrada em cada bar. O resto da divisão é distribuído entre alguns bares aleatoriamente.
- Para nao gerar todos os entregadores no mesmo ponto, gera posições ao redor dos bares usando uma distribuição normal com desvio padrão de 500 metros.
- Ajusta cada posição para algum ponto da aresta (rua) mais proxima usando a malha viária do OpenStreetMap, via OSMnx.
- Permite salvar os resultados em CSV pela opção **Salvar CSVs desta geração**.
- Indexa os entregadores em uma Trie compacta e utiliza a Frota para organizar os resultados das rotas.
- Calcula a distância pelas ruas até o restaurante selecionado.
- Estima o tempo utilizando a velocidade de cada trecho do percurso.
- Apresenta os resultados em uma tabela ordenada pela distância viária.

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

O módulo `src/grafo.py` obtém a malha viária de Belo Horizonte com o OSMnx, utilizando o tipo de rede `drive`. Essa escolha permite trabalhar com uma rede destinada à circulação de veículos e aproveitar as funções da biblioteca para obtenção, simplificação e cálculo dos percursos.

O grafo é dirigido para representar os sentidos disponíveis e é reprojetado para `EPSG:31983`, permitindo trabalhar com posições em metros. As arestas são identificadas por `(u, v, key)`: a chave distingue possíveis arestas paralelas entre os mesmos nós, e o atributo `length` representa o comprimento utilizado nas rotas.

A malha é salva em `data/malha_bh_drive_31983.graphml` e reutilizada nas execuções seguintes. O armazenamento local evita repetir o download e o processamento inicial, além de permitir utilizar a mesma malha durante os testes.

## Geocodificador

O script `scripts/geocodificador.py` busca coordenadas para os endereços de `data/bares.csv` e grava o resultado em `data/bares_com_coordenadas.csv`. Ele consulta o OpenStreetMap endereço por endereço e inclui uma pausa entre as consultas, pode levar horas para terminar

## Configurações

`utilities/constants.py` centraliza os caminhos, o desvio padrão e os sistemas de coordenadas utilizados pelo app e pelo simulador. O arquivo de entrada padrão é `data/bares.csv`, e o desvio padrão da geração é de 500 metros.

## Estrutura do projeto

```text
tropafood/
├── app.py                       # Interface interativa em Dash
├── assets/style.css             # Estilos da interface
├── data/                        # Bases, resultados e cache local do grafo
├── docs/
│   ├── tp1.pdf                  # Enunciado do trabalho
│   ├── analise_experimental.md  # Análise das consultas
│   └── experimentos/            # Medições e reprodução dos experimentos
├── entities/                    # Entidades de restaurantes e entregadores
├── scripts/geocodificador.py    # Geocodificação de endereços
├── src/
│   ├── grafo.py                 # Carregamento ou geração da malha viária
│   ├── simulador.py             # Geração e ajuste das posições
│   ├── geohash.py               # Estrutura de geohash
│   ├── trie.py                  # Estrutura Trie
│   ├── frota.py                 # Organização dos entregadores e resultados
│   └── rotas.py                 # Cálculo de distância e tempo pelas ruas
├── utilities/
│   ├── constants.py             # Configurações compartilhadas
│   ├── files.py                 # Leitura de dados e criação das entidades
│   ├── indice.py                # Construção e reutilização das Tries por geração
│   └── interface.py             # Filtros, mapa e tabela de resultados
├── dockerfile              
├── main.py                  
└── requirements.txt
```

# Documentação Detalhada

## 1. Introdução

O Tropafood é uma aplicação interativa para simular a localização de entregadores e consultar sua proximidade em relação a restaurantes de Belo Horizonte. As posições são geradas ao redor dos restaurantes e corrigidas para ruas transitáveis. A consulta combina a indexação espacial por Geohash e Trie compacta, a filtragem por raio geográfico e o cálculo de percursos pela malha viária. Os resultados são apresentados no mapa e em uma tabela ordenada pela distância pelas ruas, acompanhada da estimativa de tempo de chegada.

A base de restaurantes utilizada é `data/bares.csv`, com 20.859 registros provenientes da publicação de setembro de 2026 do conjunto [Atividade Econômica da Prefeitura de Belo Horizonte](https://dados.pbh.gov.br/pt_BR/dataset/atividade-economica). A preparação no QGIS acrescentou os campos `LATITUDE` e `LONGITUDE`, preservando os atributos e a geometria originais. Assim, os dados de identificação e as representações espaciais permanecem associados na mesma tabela. As unidades e os sistemas de coordenadas utilizados são descritos na seção do simulador.

## 2. Indexação Geohash

*Geohashing* é um método de indexação capaz de converter coordenadas geográficas, como latitude e longitude, para uma string. A ideia é justamente converter duas dimensões (x, y) para uma única dimensão z. Essa string é definida na base 32 (`todos os números de 0-9 e letras do alfabeto - (a, l, i, o`), consistindo de 8 níveis na nossa implementação.

O algoritmo funciona da seguinte forma: Definimos limites superiores e inferiores para a latitude e longitude da terra, respectivamente $[-90, 90]$ e $[-180, 180]$, e então começamos a definir uma cadeia binária $Z$, que será constituida intercalando bits de longitude e latitude a cada iteração. Ao final, como queremos 8 caracteres na base 32, temos que ter um total de 40 bits, ou seja, vamos realizar 20 intercalações, nas quais cada uma adiciona 2 bits (longitude e latitude).

A intercalação funciona da seguinte forma (tanto para a longtitude quanto para a latitude, comparados com os seus respectivos limites):

1. Calculamos a coordenada média (ex: `long_mid = (long_upper + long_lower)/2`)
2. Checamos se a coordenada é maior ou menor que a coordenada média:
   1. se for maior ou igual, então devemos subir o limite inferior da coordenada e adicionar 1 na cadeia binária $Z$.
   2. se for menor, então devemos reduzir o limite superior da coordenada e adicionar 0 na cadeia binária $Z$.

A ideia é ter uma cadeia que represente a seguinte malha:

![1792531821498](image/README/1792531821498.png)

Ao final da intercalação, teremos uma cadeia de 40 bits intercados (20 de longitude e 20 de latitude). Agora, precisamos converter essa string binária para a base 32 e obter o geohash. Podemos fazer isso transformando cada 5 bits de $Z$ em um caractere base32.

Ao final, teremos uma indexação de 8 caracteres, como por exemplo: "7h2whsem". Essa string é referente à seguinte região em um mapa:
![1792532107160](image/README/1792532107160.png)

Assim como foi necessário definir a codificação das coordenadas para o Geohash, também foi preciso realizar a engenharia reversa e descodificar um geohash. Isso para quando precisamos buscar um restaurante a partir do seu geohash. A lógica é bem simples, é literalmente desfazer todos os passos que fizemos para sair de uma coordenada para chegar até o geohash.

## 3. Árvore Trie Compacta

A árvore Trie Compacta, é uma estrutura de dados vista nas aulas que é, em essência uma árvore de prefixos. A ideia é armazenar strings de uma forma que seja fácil encontrar strings com prefixos iguais. Em nosso código, os seus nós são representados pela classe *TrieNode* que é composta por 3 atributos:

- *rotulo:* é a string armazenada naquele nó; (maior diferença em relação a Trie normal, aqui nós guardamos strings, e não somente o caractere)
- *filhos:* é um dicionário contendo os nós-filho daquele nó;
- *entregadores:* é uma lista dos entregadores que estão vinculados àquele rótulo terminal. Note que um entregador só constará na lista se o seu geohash terminar a sua inserção na Trie naquele nó. Esse atributo pode ser utilizado para saber se aquele nó é um nó com valor (possui entregador) ou não, basta verificar se a lista está vazia ou não.

Além disso, nós implementamos dois métodos para a classe *TrieCompacta:*

*1. insert(entregador): $O(m)$, tal que m é o tamanho da string.* É responsável por inserir o geohash do entregador passado como parâmetro, vamos chamar de $g$ na árvore. Percorremos a árvore toda, partindo da raiz e consumindo a string $g$ com o passar dos nós. A ideia é, estando no nó atual, sempre buscar se existe algum filho com o caractere inicial que bate com o caractere na posição [0] do fragmento da cadeia $g$ que ainda não foi consumido.

Se não existir, então cria-se um nó filho na Trie com todo o rótulo restante.

Se existir, então  caminhamos até o filho e avaliamos como ele consegue consumir completamente o fragmento de $g$. Nós usamos uma função capaz de encontrar o maior prefixo entre duas strings. $O(min(s_1, s_2))$.

- Se o fragmento completamente consumido e o seu tamanho for igual ao do rótulo no nó, isso quer dizer que esse nó possui valor e deve adicionar o entregador que possui aquele geohash $g$ na lista de entregadores.
- Se o fragmento foi parcialmente consumido, então deve-se o nó da seguinte forma: definir dois filhos e um pai. O pai conterá como rótulo o prefixo em comum entre o fragmento de $g$ e o rótulo do nó antigo. O restante do rótulo do nó antigo e o restante não consumido de $g$ devem ser nós-filho.

2. *search(geohash): $O(m + k)$, tal que m é o tamanho da string.* Na busca, queremos buscar quais os entregadores referentes a um determinado geohash. Note que aqui existe uma sacada: Um geohash que é completamente consumido em um vértice pai deve considerar todos os entregadores dos filhos também, pois estes estão contidos no geohash pai. A busca funciona de forma parecida com a inserção, nós vamos percorremos a string $g$. até que seja completamente consumida dentro da árvore. Se não conseguimos, então retornamos uma lista vazia e a busca falha. Se conseguimos, temos que buscar todos os entregadores daquele nó, considerando também os filhos dele. Fazemos isso utilizando recursividade, parecido com uma DFS $O(k)$, tal que temos $k$ entregadores encontrados, que agrega os entregadores de cada nó.

### 3.1 Busca por restaurantes

Depois de já termos definido a nossa Trie Compacta, é necessário buscar um restaurante, utilizando a sua coordenada convertida para geohash. No entanto, buscar pelo geohash exato do restaurante pode restringir demais a busca e, portanto, nós selecionamos os 6 primeiros caracteres do código geohash do restaurante, para que assim, uma área maior fosse contemplada (região/bairro onde o restaurante se encontra). 

A lógica é simples: temos que percorrer os nós até consumir os 6 caracteres do geohash reduzido. Dessa forma, quando a cadeia for completamente consumida, vai parar em um nó pai e então coletamos todos os filhos, que são entregadores dentro da região delimitada. É simplesmente a aplicação do método .search explicado no bloco anterior.

Além disso, temos que procurar entregadores nos blocos adjacentes, o que será discutido no próximo tópico.

### 3.2 Como tratar pontos adjacentes muito próximos?

A solução que encontramos para tratar pontos que estão muito próximos uns dos outros é dado a posição de um restaurante, buscarmos nas 8 malhas adjacentes à ele:

![1792544891235](image/README/1792544891235.png)

Nós fazemos isso da seguinte forma: Decodificamos o geohash do restaurante, encontrando a sua coordenada em latitude e longitude. Depois disso, calculamos quais as coordenadas do seu centro e qual o erro em relação aos diferentes pontos centrais de cada um dos quadrantes adjacentes. Depois de encontrar os centros, nós podemos calcular os seus respectivos geohashes e efetuamos a busca neles também, a fim de garantir que não perdemos nenhum ponto que estava muito perto do restaurante, mas que não se encontrava no mesmo quadrante.

## 4. Simulador de Geração de Entregadores

A modulo `src/simulador.py` contém a geração e a correção das posições dos entregadores, distribuindo os entregadores equitativamente entre os restaurantes por meio de uma distrbuição normal centrada em cada um dos restaurantes.

### 4.1 Distribuição Espacial Baseada em Demanda

A função `gerar_entregadores_normais` é responsável pela geração da posição inicial dos entregadores. Dado N sendo o Número de Entregadores a serem gerados e M o número de restaurante, a geração é feita da seguinte forma:

- lê a geometria de cada bar e usa suas coordenadas $x$, $y$, projetadas em metros como centro da distribuição normal.
- A quantidade solicitada é dividida entre os bares: todos recebem a mesma inteira quantidade $E$, obtida através de $\lfloor N/M \rfloor$, e o resto R, caso a divisão não seja inteira, é distribuído aleatoriamente entre alguns bares.
- Para cada entregador, as coordenadas x e y são sorteadas independentemente por distribuições normais centradas no restaurante, com o desvio padrão configurado, de 500 metros por eixo na configuração utilizada.

Cada entregador recebe um ID, o nome do bar de origem, as coordenadas matemáticas em metros (`EPSG:31983`) e sua conversão para latitude e longitude (`EPSG:4326`).

Como o exemplo a seguir mostra, essa geração ainda não é a ideal, uma vez que nem todos os pontos gerados respeitam a malha viária, como no exemplo a seguir, os pontos circulados foram plotados fora das ruas da malha, inclusive dentro do Parque Municipal Américo Renné.

**Pontos em Vermelho: Entregadores**
**Pontos em Azul: Restaurantes**

![alt text](assets/images/frota_mat.png)

O desvio padrão controla a dispersão das posições ao redor dos restaurantes. Os 500 metros são uma medida dessa dispersão por eixo e não representam uma distância máxima para a geração.

Latitude e longitude são mantidas em `EPSG:4326`, em graus, para a exibição no mapa e a codificação Geohash. Dessa forma, cada representação atende a uma finalidade: coordenadas métricas para geração e operações sobre as ruas, e coordenadas geográficas para apresentação e indexação.

A geometria e a latitude/longitude permanecem na mesma tabela para preservar a associação com os dados do restaurante. O formato `POINT`, por si só, não determina a unidade da geometria; essa unidade depende do sistema de coordenadas adotado.

### 4.2 Restrição Viária (Realismo Geográfico)

Como mencionado, a geração acima é feita com base em uma distribuição normal matemática, fatalmente haverá entregadores com coordenadas irreais, e.g. no meio da Lagoa da Pampulha, em cima de telhados, etc. Por isso, foi criada a função `corrigir_para_ruas`, que aloca os entregadores para posições válidas dentro de ruas reais.

A função `corrigir_para_ruas` recebe a tabela com os entregadores e suas posições matemáticas e, para cada entregador, consulta a aresta da malha viária de BH mais próxima de cada posição matemática com o OSMnx. Em seguida, projeta o ponto com coordenadas $x$ e $y$ em metros na rua usando o Shapely e transforma as coordenadas resultantes para latitude e longitude. Dessa forma, a posição corrigida pode ser exibida sobre a malha viária.

Para encaixar os entregadores sobre a linha real das ruas, a função chama `nearest_edges` do osmnx, que identifica o trecho de rua mais próximo de cada ponto matemático. A partir daí, é extraída a geometria da rua. Utilizando o Shapely, o ponto é projetado sobre essa linha: o método `project` descobre a posição exata ao longo do trecho e o `interpolate` pega as novas coordenadas. Como toda essa operação ocorre em metros `EPSG:31983`, as distâncias e projeções são tratadas em metros. Por fim, as coordenadas corrigidas são convertidas para graus (latitude e longitude `EPSG:4326`) para a renderização no mapa da interface.

Além das coordenadas corrigidas, são armazenados os campos `aresta_u`, `aresta_v`, `aresta_key` e `posicao_aresta_metros`. Eles identificam a aresta associada ao entregador e sua posição ao longo da geometria orientada de u para v.

Preservar essas informações permite reutilizar a associação com a rua nas consultas posteriores e representar o entregador no meio de um trecho, sem restringir sua posição aos cruzamentos.

A seguir, temos um exemplo da geração com a correção aplicada, onde todos os entregadores são plotados dentro das ruas.

**Pontos em Vermelho: Entregadores Corrigidos na Malha Viária**

**Pontos em Azul: Restaurantes**

![alt text](assets/images/frota_rua.png)

O simulador, além de utilizado na interface, pode ser executado pelo terminal. Nesse modo, ele solicita a quantidade de entregadores e grava os CSVs matemáticos e corrigidos nos caminhos padrão definidos em `utilities/constants.py`.

Em `utilities/files.py`, a geometria dos restaurantes é interpretada para preencher suas coordenadas x e y. Os entregadores são criados com as coordenadas corrigidas e os metadados da aresta, preservando essas informações desde a leitura dos dados até o cálculo das rotas.

### 4.3 Benchmark Simulador

O benchmark (`scripts/benchmark_frota.py`) mede separadamente a geração e a correção para ruas com 1.000, 10.000, 100.000 e 1.000.000 de entregadores. Usa os bares de `data/bares.csv` e executa cada tamanho cinco vezes. Os testes foram executados em uma máquina com i7 13th, 32ram, 512ssd e windows 11:

#### 4.3.1 Análise assintótica

**Geração dos Entregadores:**

Para M restaurantes e N entregadores, a geração percorre os restaurantes e cria N registros, resultando em tempo O(M + N) e memória O(M + N). Com a base fixa, seu custo é O(N).

**Correção para a Malha Viária:**

Na correção, cada entregador é consultado na malha e projetado na rua mais próxima. Para uma malha fixa, podemos afirmar um possível crescimento linear O(N).

#### 4.3.2 Análise empírica

A leitura do CSV de bares e o carregamento da malha são feitos antes da medição. A geração inclui a conversão das coordenadas de metros para graus e a correção inclui a busca da aresta mais próxima, a projeção na rua e a conversão das coordenadas.
As médias são gravadas em `data/benchmark_frota.csv`.

Segue abaixo os tempos obtidos ao executar o benchmark na máquina citada anteriormente:

| Entregadores | Geração (s) | Correção para ruas (s) |
| -----------: | --------: | -------------------: |
|        1.000 |     0,729 |                0,923 |
|       10.000 |     0,766 |                1,545 |
|      100.000 |     1,176 |                8,103 |
|    1.000.000 |     5,394 |               72,169 |

Ao aumentar a frota de 1.000 para 1.000.000 de entregadores (1.000 vezes), o
tempo medido aumentou cerca de 7,4 vezes na geração e 78 vezes na correção.
O crescimento observado foi sublinear nessa faixa de teste, mas isso não
determina a complexidade assintótica: custos fixos e características do ambiente
influenciam os tempos medidos.

## 5. Interface do mapa

O mapa da aplicação é construído com Dash e Plotly, utilizando traços `Scattermap` para exibir os pontos sobre a cartografia de fundo. Os entregadores são representados por marcadores circulares posicionados nas coordenadas corrigidas para as ruas; ao passar o cursor sobre um marcador, são exibidos o ID, a latitude e a longitude do entregador.

É possível buscar um restaurante pelo nome e definir um raio de busca em metros. O valor deve estar entre 100 e 50.000 metros; caso contrário, a interface informa que o raio é inválido. Ao selecionar um restaurante, o mapa o destaca com um marcador e centraliza a visualização nele. Os entregadores selecionados pela busca e pelo filtro de raio ficam verdes, enquanto os descartados permanecem vermelhos. O resumo informa quantos entregadores estão dentro do raio em relação ao total exibido. A opção **Exibir raio de busca** desenha a área circular configurada no mapa.

![alt text](assets/images/filtrados.png)

A opção **Exibir todos os restaurantes** adiciona ao mapa os demais restaurantes. Sem um restaurante selecionado, os entregadores aparecem em vermelho. O mapa é exibido desde a abertura da aplicação. Os entregadores aparecem após a geração de uma frota.

**Apenas Entregadores**
![alt text](assets/images/entregadores.png)

**Apenas Restaurantes**
![alt text](assets/images/restaurantes.png)

## 6. Aplicação web

A aplicação roda em Dash através do `app.py`. Nela, o usuário informa a quantidade desejada de entregadores e clica para gerar a frota, que é corrigida para a malha viária e exibida no mapa. 

Há uma opção de salvar a geração em CSV (posições originais e corrigidas), salvando os arquivos com data e hora para não sobrescrever dados antigos. 

Ao escolher um restaurante, a aplicação consulta a Trie para recuperar candidatos e depois aplica o raio de busca pela distância geográfica, calculada com `great_circle`, do OSMnx, a partir das coordenadas de latitude e longitude. Somente os entregadores selecionados seguem para o cálculo das rotas.

O raio define a proximidade geográfica em relação ao restaurante. A distância apresentada na tabela corresponde ao percurso pelas ruas, respeitando as conexões e os sentidos disponíveis na malha. Por isso, com um raio de 2.000 metros, um entregador pode ser selecionado e apresentar um percurso viário superior a 2.000 metros. Não é aplicado um segundo filtro para limitar o comprimento da rota ao valor do raio. A tabela ordena os selecionados pela distância viária e apresenta o tempo estimado desse mesmo percurso.

O botão **Mostrar tabela** abre os resultados em um painel separado, com mais espaço para leitura das colunas. O botão **Fechar** recolhe esse painel. Essa organização mantém os controles da simulação no painel lateral e permite consultar a tabela sobre o mapa.

A função `montar_tabela_rotas()`, em `utilities/interface.py`, mantém a ordenação fornecida pela Frota. A distância é apresentada em metros, e o tempo, calculado em segundos, é arredondado para o segundo mais próximo e exibido em minutos e segundos, como `2 min 30 s`. Resultados sem caminho aparecem como **Sem rota**, diferenciando essa situação de um percurso com distância zero.

## 7. Entregadores, restaurantes e organização da Frota

As classes `Entregador` e `Restaurante`, na pasta `entities/`, representam os participantes da simulação. Elas reúnem os dados de cada participante, enquanto a geração das posições, a busca e o cálculo dos percursos ficam nos módulos responsáveis por essas operações.

O `Entregador` possui um identificador, coordenadas geográficas, coordenadas métricas, Geohash e informações sobre sua posição na aresta. O identificador permite associar cada resultado ao entregador correto, mesmo depois da ordenação da tabela. A posição utilizada é a corrigida para as ruas, conforme explicado na seção de restrição viária.

O `Restaurante` possui identificador, nome, endereço e coordenadas. Sua localização serve como centro da distribuição dos entregadores e como referência para as consultas. No cálculo das rotas, suas coordenadas métricas são usadas para localizar o destino na malha viária. Um entregador pode ser consultado em relação a qualquer restaurante, independentemente daquele utilizado na geração de sua posição.

As funções de `utilities/files.py` fazem a conversão dos registros em objetos dessas classes. `ler_bares()` interpreta a geometria do CSV para criar os restaurantes, enquanto `ler_entregadores()` e `criar_entregadores()` criam entregadores a partir do CSV ou dos registros da geração. Na interface, os restaurantes são consultados diretamente na tabela carregada com pandas, e os objetos `Entregador` são criados para trabalhar com a Frota.

A classe `Frota`, em `src/frota.py`, reúne os entregadores selecionados para o cálculo das rotas e organiza os resultados apresentados na interface. A construção e a reutilização do índice espacial ficam no módulo `utilities/indice.py`.

Cada geração recebe um identificador próprio. A função `obter_trie_entregadores()` utiliza esse identificador para construir a Trie com as posições corrigidas e reutilizá-la nas atualizações do mapa, do resumo e da tabela. Dessa forma, trocar o restaurante ou o raio não exige reinserir todos os entregadores no índice. O servidor mantém até oito gerações em memória e remove a menos recentemente utilizada ao ultrapassar esse limite. Se um índice não estiver mais disponível, ele é reconstruído a partir dos registros da geração. Um bloqueio evita construções simultâneas do mesmo índice por callbacks concorrentes.

O método `_localizar_entregador()` prepara a posição de cada entregador na malha, aproveitando a identificação da aresta armazenada. Quando todos os identificadores estão ausentes, procura a rua mais próxima; quando estão parcialmente preenchidos, informa o problema.

O método `calcular_rotas()` recebe o grafo, as coordenadas métricas do restaurante e uma lista de entregadores selecionados. Ele solicita os percursos ao módulo de rotas, associa os resultados aos IDs e depois ordena pela distância.

Essa divisão permite que a seleção espacial forneça os candidatos, que o módulo de rotas calcule os percursos e que a Frota organize os resultados para a interface. A associação aos IDs acontece antes da ordenação para preservar a correspondência entre cada entregador e suas medidas.

Os resultados são retornados em novos registros, sem modificar os objetos originais. Quando não existe caminho, distância e tempo recebem `None`, e o entregador fica ao final da lista.

## 8. Cálculo das rotas e do tempo

O módulo `src/rotas.py` calcula os percursos utilizando a malha viária. A distância pelas ruas foi escolhida porque a proximidade geográfica não representa necessariamente o deslocamento disponível: um entregador pode precisar contornar um quarteirão ou seguir outro sentido de circulação.

A função `obter_geometria_aresta()` recupera o traçado de uma aresta existente e o orienta de u para v. Quando não há geometria explícita, utiliza um segmento entre esses nós. Esse procedimento representa uma conexão já existente no grafo, sem criar uma rua nova. As curvas dos trechos unidos pela simplificação do OSMnx são preservadas na geometria resultante.

![Conferência da geometria das ruas no QGIS](assets/images/malha_geometria_qgis.png)

Conferência da malha viária no QGIS sobre o mapa do OpenStreetMap. Em azul, uma amostra de arestas com curvas preservadas; em laranja, segmentos entre os nós de arestas sem geometria explícita. A inspeção permite comparar os traçados do grafo com as vias representadas no mapa.

Base cartográfica: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

A função `calcular_rotas_osmnx()` utiliza a busca de menor caminho do OSMnx com o peso `length`. Como entregadores e restaurantes podem estar no meio das ruas, são adicionados nós e conexões em uma cópia temporária do grafo. Isso permite considerar os trechos parciais de saída e chegada e preservar a malha original. Também é tratado o caso em que origem e destino estão na mesma aresta.

Para estimar o tempo, a função `preparar_tempos()`, em `src/grafo.py`, acrescenta os atributos `speed_kph`, em km/h, e `travel_time`, em segundos. A preparação utiliza as velocidades informadas no OSM e estima os valores ausentes com base nas velocidades disponíveis e na categoria da via.

O tempo dos trechos parciais é calculado utilizando a velocidade da aresta correspondente. Ao percorrer a rota, distância e tempo são somados sobre as mesmas arestas, inclusive quando existem arestas paralelas. Isso evita combinar a distância de uma via com o tempo de outra.

O critério da busca continua sendo a menor distância. O tempo apresentado corresponde a esse mesmo percurso, sem uma busca separada pela rota mais rápida. A estimativa não considera trânsito, semáforos, paradas ou preparação do pedido.

As verificações realizadas incluíram trechos parciais, sentidos disponíveis, pontos nos extremos, arestas paralelas e ausência de caminho. Também foram conferidas a associação dos resultados aos IDs, a ordenação e a atualização das consultas sem regenerar as posições dos entregadores.

## 9. Análise experimental das consultas

Os experimentos foram realizados em 20/10/2026, em um Mac com Apple M4, 10 núcleos, 16 GiB de memória e macOS 27.0.1, utilizando a imagem Docker `tropafood-app`, com Linux ARM64, Python 3.10.22, OSMnx 2.0.7 e Dash 4.4.1. Foi utilizada a base completa de 20.859 restaurantes e a malha local com 32.781 nós e 83.993 arestas dirigidas.

Foram geradas frotas de 1.000 e 5.000 entregadores, com desvio padrão de 500 metros. Para permitir a reprodução dos resultados, foi utilizada a semente `20261020 + N`, em que `N` é o tamanho da frota. A geração, a correção para as ruas e a construção inicial da Trie foram realizadas antes das medições. As consultas de uma mesma frota reutilizaram os mesmos entregadores e o mesmo índice.

Cada cenário foi executado uma vez para aquecimento e depois repetido cinco vezes. O tempo foi medido com `perf_counter`, realizando dois pedidos locais aos callbacks reais do Dash, pelo cliente de teste do Flask: primeiro mapa e resumo; depois tabela e rotas. A coluna **Total** é a soma desses processamentos em sequência. Ela inclui a serialização local dos pedidos e respostas e, na tabela, o carregamento e a preparação da malha feitos pela aplicação em cada consulta. Não inclui geração da frota, aquecimento, download inicial da malha, comunicação de rede ou renderização no navegador. Na interface, os callbacks podem executar em paralelo; portanto, esse total não representa diretamente o tempo entre um clique e o fim da atualização visual.

Os restaurantes consultados foram **NECTAR DA SERRA LTDA**, no bairro Cruzeiro, e **BAR E CAFE DONATELO LTDA**, no Jardim Atlântico. Os tempos abaixo são médias em segundos; a coluna **Sem rota** está incluída no total de selecionados.

| Caso | Frota | Restaurante | Raio (m) | Selecionados | Sem rota | Mapa e resumo (s) | Tabela e rotas (s) | Total (s) |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | 1.000 | Néctar da Serra | 1.000 | 7 | 0 | 0,042 | 4,583 | 4,625 |
| C2 | 5.000 | Néctar da Serra | 1.000 | 34 | 0 | 0,181 | 4,563 | 4,745 |
| C3 | 5.000 | Néctar da Serra | 2.000 | 171 | 2 | 0,187 | 4,772 | 4,959 |
| C4 | 5.000 | Donatelo | 2.000 | 176 | 0 | 0,181 | 4,801 | 4,982 |
| C5 | 5.000 | Néctar da Serra | 100 | 1 | 0 | 0,182 | 4,621 | 4,803 |

Os intervalos observados para o tempo total foram: C1: 4,577 a 4,713 s; C2: 4,715 a 4,790 s; C3: 4,852 a 5,007 s; C4: 4,961 a 5,040 s; C5: 4,743 a 4,840 s. As repetições de cada cenário retornaram os mesmos IDs, distâncias e tempos estimados.

Comparando C1 e C2, o aumento da frota de 1.000 para 5.000 entregadores elevou o número selecionado de 7 para 34, mantendo o restaurante e o raio. Comparando C2 e C3, o aumento do raio de 1 km para 2 km elevou a seleção de 34 para 171 entregadores. C3 e C4 mostram resultados diferentes para dois restaurantes com a mesma frota e o mesmo raio, conforme a distribuição espacial dos entregadores.

A etapa de tabela e rotas concentrou a maior parte do tempo nos cenários medidos. Ela inclui o carregamento da malha e a preparação das velocidades e dos tempos, além do cálculo dos caminhos. Mesmo C5, com apenas um selecionado, apresentou esse custo. Esses resultados descrevem os cenários e o ambiente utilizados; não determinam, por si só, a complexidade assintótica nem o desempenho para qualquer tamanho de frota.

**Raio geográfico e distância pelas ruas.** Em C3, 169 dos 171 selecionados tiveram caminho encontrado; os outros dois foram apresentados como **Sem rota**. Entre os 169 caminhos, 84 ultrapassaram os 2.000 metros do raio. Por exemplo, o `entregador_1662` estava a aproximadamente **1.794,3 metros de distância geográfica** do restaurante, mas seu percurso pelas ruas foi de **2.594,8 metros**, com estimativa de **2 min 48 s**. Ele permaneceu no resultado porque a seleção utiliza o raio geográfico, enquanto a tabela informa o percurso viário. O limite do raio não é reaplicado como limite de comprimento da rota.

**Registros da interface.** As imagens foram obtidas em uma instância separada da mesma aplicação, com as mesmas sementes de geração. A consulta C1 teve seus sete resultados conferidos; em C3, foram conferidos a contagem de 171 registros, o exemplo acima e os dois casos sem rota. Em C4, os 176 IDs, comprimentos de rota e tempos exibidos foram comparados aos registros do experimento. O ajuste da semente foi feito somente no processo usado para produzir as imagens, sem modificar o código da aplicação.

![Consulta C1: 1.000 entregadores e raio geográfico de 1.000 metros](assets/images/experimentos/consulta_c1.jpg)

Consulta C1 com os sete selecionados e a tabela ordenada pela distância viária.

![Consulta C3: mapa com 5.000 entregadores e raio geográfico de 2.000 metros](assets/images/experimentos/consulta_c3_mapa.jpg)

Consulta C3 com o raio geográfico e 171 entregadores selecionados pelos filtros.

![Consulta C3: tabela rolada até o entregador com percurso de 2.594,8 metros](assets/images/experimentos/consulta_c3_tabela.jpg)

Detalhe da tabela de C3, rolada até o `entregador_1662`. A coluna de distância viária mostra 2.594,8 metros, embora o raio selecionado seja de 2.000 metros.

![Consulta C4: resultados no Bar e Café Donatelo](assets/images/experimentos/consulta_c4.jpg)

Consulta C4 com 176 selecionados em outra região de Belo Horizonte.

Os [resultados consolidados](docs/experimentos/saidas/resultados_consultas.csv), os [tempos das 25 medições](docs/experimentos/saidas/tempos_brutos.csv), as frotas e os detalhes por entregador estão em `docs/experimentos/saidas/`. O [script de medição](docs/experimentos/medir.py) e o registro do ambiente acompanham os resultados. Os comprimentos de rota registrados nos detalhes têm a precisão exibida pela tabela, de uma casa decimal.

## INTEGRANTES

- Marney Santos de Melo — 2024106034
- Rafael Resende Miranda — 2024065990
- Victor Murilo Kaizer — 2024096551
