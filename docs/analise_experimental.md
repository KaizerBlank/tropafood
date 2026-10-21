## 9. Análise experimental das consultas

Os experimentos foram realizados em 20/10/2026, em um Mac com Apple M4, 10 núcleos, 16 GiB de memória e macOS 27.0.1, utilizando a imagem Docker `tropafood-app`, com Linux ARM64, Python 3.10.22, OSMnx 2.0.7 e Dash 4.4.1. Foi utilizada a base completa de 20.859 restaurantes e a malha local com 32.781 nós e 83.993 arestas dirigidas.

Foram geradas frotas de 1.000 e 5.000 entregadores, com desvio padrão de 500 metros. Para permitir a reprodução dos resultados, foi utilizada a semente `20261020 + N`, em que `N` é o tamanho da frota. A geração, a correção para as ruas e a construção inicial da Trie foram realizadas antes das medições. As consultas de uma mesma frota reutilizaram os mesmos entregadores e o mesmo índice.

Cada cenário foi executado uma vez para aquecimento e depois repetido cinco vezes. O tempo foi medido com `perf_counter`, realizando dois pedidos locais aos callbacks reais do Dash, pelo cliente de teste do Flask: primeiro mapa e resumo; depois tabela e rotas. A coluna **Total** é a soma desses processamentos em sequência. Ela inclui a serialização local dos pedidos e respostas e, na tabela, o carregamento e a preparação da malha feitos pela aplicação em cada consulta. Não inclui geração da frota, aquecimento, download inicial da malha, comunicação de rede ou renderização no navegador. Na interface, os callbacks podem executar em paralelo; portanto, esse total não representa diretamente o tempo entre um clique e o fim da atualização visual.

Os restaurantes consultados foram **NECTAR DA SERRA LTDA**, no bairro Cruzeiro, e **BAR E CAFE DONATELO LTDA**, no Jardim Atlântico. Os tempos abaixo são médias em segundos; a coluna **Sem rota** está incluída no total de selecionados.

| Caso | Frota | Restaurante | Raio (m) | Selecionados | Sem rota | Mapa e resumo (s) | Tabela e rotas (s) | Total (s) |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | 1.000 | Néctar da Serra | 1.000 | 11 | 0 | 0,042 | 4,623 | 4,664 |
| C2 | 5.000 | Néctar da Serra | 1.000 | 38 | 0 | 0,185 | 4,714 | 4,899 |
| C3 | 5.000 | Néctar da Serra | 2.000 | 187 | 2 | 0,187 | 4,837 | 5,024 |
| C4 | 5.000 | Donatelo | 2.000 | 178 | 0 | 0,183 | 4,778 | 4,961 |
| C5 | 5.000 | Néctar da Serra | 100 | 1 | 0 | 0,201 | 5,326 | 5,527 |

Os intervalos observados para o tempo total foram: C1: 4,586 a 4,865 s; C2: 4,823 a 5,001 s; C3: 4,908 a 5,118 s; C4: 4,888 a 5,055 s; C5: 4,827 a 6,177 s. As repetições de cada cenário retornaram os mesmos IDs, distâncias e tempos estimados. Em cada consulta, os IDs da tabela e dos marcadores verdes foram comparados a uma referência que calcula o raio sobre toda a frota, sem utilizar a Trie. Nos cinco cenários, não houve entregadores faltando nem excedentes em relação a essa referência. Essa validação ocorreu fora da janela de medição.

Comparando C1 e C2, o aumento da frota de 1.000 para 5.000 entregadores elevou o número selecionado de 11 para 38, mantendo o restaurante e o raio. Comparando C2 e C3, o aumento do raio de 1 km para 2 km elevou a seleção de 38 para 187 entregadores. C3 e C4 mostram resultados diferentes para dois restaurantes com a mesma frota e o mesmo raio, conforme a distribuição espacial dos entregadores.

A etapa de tabela e rotas concentrou a maior parte do tempo nos cenários medidos. Ela inclui o carregamento da malha e a preparação das velocidades e dos tempos, além do cálculo dos caminhos. Mesmo C5, com apenas um selecionado, apresentou esse custo. Esses resultados descrevem os cenários e o ambiente utilizados; não determinam, por si só, a complexidade assintótica nem o desempenho para qualquer tamanho de frota.

**Raio geográfico e distância pelas ruas.** Em C3, 185 dos 187 selecionados tiveram caminho encontrado; os outros 2 foram apresentados como **Sem rota**. Entre os 185 caminhos, 94 ultrapassaram os 2.000 metros do raio. Por exemplo, o `entregador_1662` estava a aproximadamente **1.794,3 metros de distância geográfica** do restaurante, mas seu percurso pelas ruas foi de **2.594,8 metros**, com estimativa de **2 min 48 s**. Ele permaneceu no resultado porque a seleção utiliza o raio geográfico, enquanto a tabela informa o percurso viário. O limite do raio não é reaplicado como limite de comprimento da rota.

**Registros da interface.** As imagens foram obtidas em uma instância separada da mesma aplicação, com as mesmas sementes de geração. Os IDs, comprimentos de rota e tempos exibidos nas consultas C1, C3 e C4 foram comparados aos registros do experimento. O ajuste da semente foi feito somente no processo usado para produzir as imagens, sem modificar o código da aplicação.

![Consulta C1: 1.000 entregadores e raio geográfico de 1.000 metros](../assets/images/experimentos/consulta_c1.jpg)

Consulta C1 com 11 selecionados e a tabela ordenada pela distância viária.

![Consulta C3: mapa com 5.000 entregadores e raio geográfico de 2.000 metros](../assets/images/experimentos/consulta_c3_mapa.jpg)

Consulta C3 com o raio geográfico e 187 entregadores selecionados pelos filtros.

![Consulta C3: tabela rolada até o entregador com percurso de 2.594,8 metros](../assets/images/experimentos/consulta_c3_tabela.jpg)

Detalhe da tabela de C3, rolada até o `entregador_1662`. A coluna de distância viária mostra 2.594,8 metros, embora o raio selecionado seja de 2.000 metros.

![Consulta C4: resultados no Bar e Café Donatelo](../assets/images/experimentos/consulta_c4.jpg)

Consulta C4 com 178 selecionados em outra região de Belo Horizonte.

Os [resultados consolidados](experimentos/saidas/resultados_consultas.csv), os [tempos das 25 medições](experimentos/saidas/tempos_brutos.csv), as frotas e os detalhes por entregador estão em `docs/experimentos/saidas/`. O [script de medição](experimentos/medir.py) e o registro do ambiente acompanham os resultados. Os comprimentos de rota registrados nos detalhes têm a precisão exibida pela tabela, de uma casa decimal.
