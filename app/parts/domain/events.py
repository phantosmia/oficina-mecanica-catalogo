from dataclasses import dataclass


@dataclass(frozen=True)
class PartRegistered:
    """Evento `PecaCadastrada` (docs/saga.md): o Estoque reage criando o saldo
    zerado da peça. Publicado via outbox, na mesma transação do cadastro."""

    part_id: str
    sku: str
    name: str

    event_type = "PecaCadastrada"

    def payload(self) -> dict[str, str]:
        return {"part_id": self.part_id, "sku": self.sku, "name": self.name}
