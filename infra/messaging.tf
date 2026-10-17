# Mensageria do serviço (RFC-0007, contrato em docs/saga.md do
# oficina-mecanica-fiap): cada serviço cria o próprio tópico de eventos, a
# própria fila de comandos e as filas com que assina tópicos de outros
# serviços. Toda fila tem uma DLQ.

resource "aws_sns_topic" "events" {
  name = "${local.prefix}-catalogo-eventos"
}
