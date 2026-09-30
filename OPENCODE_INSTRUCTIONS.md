# Instruções de Verificação

- Quando o usuário pedir fact-check de uma afirmação sem imagem, use `image_analysis_search_fact_checks` ou `image_analysis_summarize_fact_checks` antes de responder.
- Quando o usuário fornecer uma imagem e pedir verificação, use `image_analysis_compare_claim_with_image` com a afirmação e a imagem. Não substitua essa chamada por uma inspeção visual própria quando o usuário pedir MCP.
- Para uma descrição ou transcrição de imagem sem pesquisa de afirmação, use `image_analysis_analyze_image`.
- Ao receber uma imagem, leia seus bytes e passe-os como Base64 junto com o MIME type correto.
- Transcreva apenas texto legível. Indique incerteza em trechos ambíguos; não invente caracteres.
- Descreva pessoas somente por características visíveis relevantes à cena. Não tente identificar quem são nem deduzir seus nomes.
- Não trate compatibilidade visual, ausência de avaliações ou uma classificação isolada como prova conclusiva de veracidade.
- Se uma ferramenta falhar ou estiver limitada, informe o erro e não diga que a verificação foi concluída.