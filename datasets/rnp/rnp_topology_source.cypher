UNWIND [
  'Rio Branco','Porto Velho','Manaus','Boa Vista','Macapá','Belém','São Luís','Palmas','Cuiabá',
  'Goiânia','Campo Grande','Brasília','São Paulo','Rio de Janeiro','Belo Horizonte','Vitória',
  'Florianópolis','Porto Alegre','Recife','João Pessoa','Maceió','Aracaju','Salvador','Natal',
  'Fortaleza','Teresina','Curitiba','Campina Grande'
] AS city
CREATE (:Cidade {nome: city});

Vamos considerar os links internacionais como cidades

UNWIND [
 'RedClara/Bella-T(Am.Latina)','Monet','RedClara','SACS-WACS(Africa)',
  'Monet(EUA)','Ellalink(Europa)'
] AS city
CREATE (:Cidade {nome: city});


MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Curitiba'}) CREATE (a)-[:CONEXAO {capacidade:300}]->(b);

MATCH (a:Cidade {nome:'Curitiba'}), (b:Cidade {nome:'Florianópolis'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'Florianópolis'}), (b:Cidade {nome:'Porto Alegre'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Porto Alegre'}), (b:Cidade {nome:'RedClara/Bella-T(Am.Latina)'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Porto Alegre'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Porto Alegre'}), (b:Cidade {nome:'Curitiba'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'Florianópolis'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Curitiba'}) CREATE (a)-[:CONEXAO {capacidade:300}]->(b);

MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Monet'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'RedClara'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'Rio de Janeiro'}), (b:Cidade {nome:'Vitória'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Rio de Janeiro'}), (b:Cidade {nome:'Belo Horizonte'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'Vitória'}), (b:Cidade {nome:'Rio de Janeiro'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Salvador'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Goiânia'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Manaus'}) CREATE (a)-[:CONEXAO {capacidade:3}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Belo Horizonte'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'São Luís'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Goiânia'}), (b:Cidade {nome:'Cuiabá'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Goiânia'}), (b:Cidade {nome:'Compo Grande'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Goiânia'}),(b:Cidade {nome:'Campo Grande'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Campina Grande'}),(b:Cidade {nome:'Recife'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Fortaleza'}),(b:Cidade {nome:'Ellalink(Europa)'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Fortaleza'}),(b:Cidade {nome:'SACS-WACS(Africa)'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Fortaleza'}),(b:Cidade {nome:'Monet(EUA)'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'Fortaleza'}),(b:Cidade {nome:'Boa Vista'}) CREATE (a)-[:CONEXAO {capacidade:1}]->(b);

MATCH (a:Cidade {nome:'Fortaleza'}),(b:Cidade {nome:'Salvador'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Belo Horizonte'}),(b:Cidade {nome:'Salvador'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Natal'}),(b:Cidade {nome:'Campina Grande'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'João Pessoa'}),(b:Cidade {nome:'Campina Grande'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Rio de Janeiro'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Belo Horizonte'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Belo Horizonte'}), (b:Cidade {nome:'Vitória'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Vitória'}), (b:Cidade {nome:'Salvador'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Goiânia'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);

MATCH (a:Cidade {nome:'Fortaleza'}), (b:Cidade {nome:'Natal'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Recife'}), (b:Cidade {nome:'João Pessoa'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Recife'}), (b:Cidade {nome:'Maceió'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Maceió'}), (b:Cidade {nome:'Aracaju'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Aracaju'}), (b:Cidade {nome:'Salvador'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Fortaleza'}), (b:Cidade {nome:'Teresina'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Cuiabá'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Cuiabá'}), (b:Cidade {nome:'Campo Grande'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Campo Grande'}), (b:Cidade {nome:'Curitiba'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Palmas'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'Brasília'}), (b:Cidade {nome:'Goiânia'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);

MATCH (a:Cidade {nome:'Manaus'}), (b:Cidade {nome:'Boa Vista'}) CREATE (a)-[:CONEXAO {capacidade:1}]->(b);

MATCH (a:Cidade {nome:'Porto Velho'}), (b:Cidade {nome:'Rio Branco'}) CREATE (a)-[:CONEXAO {capacidade:6}]->(b);

MATCH (a:Cidade {nome:'Porto Velho'}), (b:Cidade {nome:'Cuiabá'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Belém'}), (b:Cidade {nome:'Macapá'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Belém'}), (b:Cidade {nome:'Palmas'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);

MATCH (a:Cidade {nome:'Manaus'}), (b:Cidade {nome:'Macapá'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);

MATCH (a:Cidade {nome:'Teresina'}), (b:Cidade {nome:'São Luís'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);

MATCH (a:Cidade {nome:'Belém'}), (b:Cidade {nome:'São Luís'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);







//Todas Ligações contrárias 

MATCH (a:Cidade {nome:'Curitiba'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:300}]->(b);
MATCH (a:Cidade {nome:'Florianópolis'}), (b:Cidade {nome:'Curitiba'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'Porto Alegre'}), (b:Cidade {nome:'Florianópolis'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'RedClara/Bella-T(Am.Latina)'}), (b:Cidade {nome:'Porto Alegre'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Porto Alegre'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Curitiba'}), (b:Cidade {nome:'Porto Alegre'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Florianópolis'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Curitiba'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:300}]->(b);
MATCH (a:Cidade {nome:'Monet'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'RedClara'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Fortaleza'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'Vitória'}), (b:Cidade {nome:'Rio de Janeiro'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Belo Horizonte'}), (b:Cidade {nome:'Rio de Janeiro'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'Rio de Janeiro'}), (b:Cidade {nome:'Vitória'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Salvador'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Goiânia'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);
MATCH (a:Cidade {nome:'Manaus'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:3}]->(b);
MATCH (a:Cidade {nome:'Belo Horizonte'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'São Luís'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Fortaleza'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'Cuiabá'}), (b:Cidade {nome:'Goiânia'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'Compo Grande'}), (b:Cidade {nome:'Goiânia'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'Campo Grande'}), (b:Cidade {nome:'Goiânia'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'Recife'}), (b:Cidade {nome:'Campina Grande'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Ellalink(Europa)'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'SACS-WACS(Africa)'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Monet(EUA)'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'Boa Vista'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:1}]->(b);
MATCH (a:Cidade {nome:'Salvador'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Salvador'}), (b:Cidade {nome:'Belo Horizonte'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Campina Grande'}), (b:Cidade {nome:'Natal'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Campina Grande'}), (b:Cidade {nome:'João Pessoa'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Rio de Janeiro'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'Belo Horizonte'}), (b:Cidade {nome:'São Paulo'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Vitória'}), (b:Cidade {nome:'Belo Horizonte'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'Salvador'}), (b:Cidade {nome:'Vitória'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'São Paulo'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);
MATCH (a:Cidade {nome:'Goiânia'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);
MATCH (a:Cidade {nome:'Natal'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'João Pessoa'}), (b:Cidade {nome:'Recife'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'Maceió'}), (b:Cidade {nome:'Recife'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Aracaju'}), (b:Cidade {nome:'Maceió'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Salvador'}), (b:Cidade {nome:'Aracaju'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Teresina'}), (b:Cidade {nome:'Fortaleza'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Cuiabá'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Campo Grande'}), (b:Cidade {nome:'Cuiabá'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Curitiba'}), (b:Cidade {nome:'Campo Grande'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'Palmas'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'Goiânia'}), (b:Cidade {nome:'Brasília'}) CREATE (a)-[:CONEXAO {capacidade:20}]->(b);
MATCH (a:Cidade {nome:'Boa Vista'}), (b:Cidade {nome:'Manaus'}) CREATE (a)-[:CONEXAO {capacidade:1}]->(b);
MATCH (a:Cidade {nome:'Rio Branco'}), (b:Cidade {nome:'Porto Velho'}) CREATE (a)-[:CONEXAO {capacidade:6}]->(b);
MATCH (a:Cidade {nome:'Cuiabá'}), (b:Cidade {nome:'Porto Velho'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Macapá'}), (b:Cidade {nome:'Belém'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Palmas'}), (b:Cidade {nome:'Belém'}) CREATE (a)-[:CONEXAO {capacidade:100}]->(b);
MATCH (a:Cidade {nome:'Macapá'}), (b:Cidade {nome:'Manaus'}) CREATE (a)-[:CONEXAO {capacidade:200}]->(b);
MATCH (a:Cidade {nome:'São Luís'}), (b:Cidade {nome:'Teresina'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
MATCH (a:Cidade {nome:'São Luís'}), (b:Cidade {nome:'Belém'}) CREATE (a)-[:CONEXAO {capacidade:10}]->(b);
