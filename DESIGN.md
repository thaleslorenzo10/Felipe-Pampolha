# Mundo visual — Felipe Pampolha 11123

O mundo já existia na peça oficial da campanha (`assets/fotos/peca-oficial.webp`). Esta página
**preserva e estende** esse sistema; não redesenha.

## Tese

O slogan da campanha é uma promessa — "O cara que resolve". A frase que ele mesmo escreveu é o
método — *"Política não se faz com promessas, se faz com escuta e respeito."* A página põe as duas
em tensão e resolve a favor da segunda: **quem resolve é quem escuta primeiro.**

Isso decide tudo. A imagem de abertura não é o retrato de estúdio da peça: é ele agachado numa rua
de terra segurando as mãos de uma senhora sentada numa cadeira de madeira. O retrato de campanha
aparece uma vez, no fim, onde ele pertence — na hora do voto.

## Paleta

Amostrada da peça oficial. Azul-marinho é o ambiente; o amarelo é reservado ao número e à ação.

| Token | Valor | Papel |
|---|---|---|
| `--navy-900` | `#0A1747` | fundo profundo, rodapé |
| `--navy-800` | `#0D1F63` | fundo de seção escura |
| `--navy-700` | `#122E86` | azul da marca, superfícies |
| `--navy-500` | `#2A55C9` | links e bordas sobre escuro |
| `--gold` | `#F7B500` | **só** número, CTA e sublinhado de ênfase |
| `--green` | `#00A551` | faixa |
| `--cyan` | `#29ABE2` | faixa, "Felipe" acima do sobrenome |
| `--orange` | `#F7941D` | faixa |
| `--paper` | `#F4F1EA` | fundo das seções claras |
| `--ink` | `#14161C` | texto sobre claro |

A **faixa tricolor** (verde / ciano / laranja, nesta ordem, sobre azul) é a assinatura gráfica da
campanha. Ela reaparece como divisor entre seções, sempre em movimento ascendente da esquerda para
a direita, como na peça. Nunca é decoração solta: só separa capítulos.

## Tipografia

- **Display:** Poppins 700/800/900, com itálico — é a letra da peça oficial ("Pampolha" em itálico
  pesado, "11123" geométrico). Tracking negativo em tamanhos grandes.
- **Texto:** Inter 400/500/600. Corpo em 18px no mobile: o público é idoso.
- Medida de 60–70ch. Sem eyebrow acima de heading.

## Motion

**Um momento autoral:** a seção do voto digita `11123` dígito a dígito, como numa urna, quando entra
na viewport — com o som visual do teclado (o dígito pousa e o próximo entra). Ensina o número em vez
de só mostrá-lo. Todo o resto é entrada discreta por fade e deslocamento curto, ease-out
exponencial, e nada disso roda sob `prefers-reduced-motion`.

## O que esta página recusa

- Cards iguais de ícone + título + texto como estrutura. As bandeiras dele são três frases de uma
  frase só — viram um bloco editorial, não uma grade.
- Números de realização, medalhas, selos: ele nunca exerceu mandato e não há o que contabilizar.
  Inventar métrica aqui seria mentir.
- Retrato de estúdio no topo. A prova da candidatura são as fotos de rua.
