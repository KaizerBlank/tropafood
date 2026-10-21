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

![Consulta C1: 1.000 entregadores e raio geográfico de 1.000 metros](../assets/images/experimentos/consulta_c1.jpg)

Consulta C1 com os sete selecionados e a tabela ordenada pela distância viária.

![Consulta C3: mapa com 5.000 entregadores e raio geográfico de 2.000 metros](../assets/images/experimentos/consulta_c3_mapa.jpg)

Consulta C3 com o raio geográfico e 171 entregadores selecionados pelos filtros.

![Consulta C3: tabela rolada até o entregador com percurso de 2.594,8 metros](../assets/images/experimentos/consulta_c3_tabela.jpg)

Detalhe da tabela de C3, rolada até o `entregador_1662`. A coluna de distância viária mostra 2.594,8 metros, embora o raio selecionado seja de 2.000 metros.

![Consulta C4: resultados no Bar e Café Donatelo](../assets/images/experimentos/consulta_c4.jpg)

Consulta C4 com 176 selecionados em outra região de Belo Horizonte.

Os [resultados consolidados](experimentos/saidas/resultados_consultas.csv), os [tempos das 25 medições](experimentos/saidas/tempos_brutos.csv), as frotas e os detalhes por entregador estão em `docs/experimentos/saidas/`. O [script de medição](experimentos/medir.py) e o registro do ambiente acompanham os resultados. Os comprimentos de rota registrados nos detalhes têm a precisão exibida pela tabela, de uma casa decimal.
