"""Preserva comentários brutos e calcula estimativa sem comentário fixado pelo bot."""
import json
from pathlib import Path
from datetime import datetime, timezone

def atualizar(path=Path("data/channel_metrics.json"), registro=Path("data/registro_formatos.json")):
    if not path.exists():
        return 0
    dados = json.loads(path.read_text(encoding="utf-8"))
    recibos = json.loads(registro.read_text(encoding="utf-8")) if registro.exists() else []
    por_media = {str(r["media_id"]): r for r in recibos if r.get("media_id")}
    n = 0
    for item in dados.get("measurements", []):
        metr = item.get("metrics") or {}
        bruto = metr.get("comments")
        if isinstance(bruto, (int, float)) and not isinstance(bruto, bool):
            # Sem ID do comentário da própria conta: uma ESTIMATIVA, nunca prova.
            desconto = min(1, max(0, int(bruto)))
            metr["comments_organic_estimate"] = max(0, int(bruto) - desconto)
            metr["auto_comments_estimate"] = desconto
            metr["comments_organic_method"] = "subtracao_estimativa_1_comentario_do_perfil"
        if str(item.get("media_id")) in por_media:
            r = por_media[str(item["media_id"])]
            item["editorial"] = {k: r.get(k) for k in (
                "formato", "gancho", "cidade_destaque", "horario_brt", "cta")}
        n += 1
    dados["organicos_atualizados_em_utc"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return n

if __name__ == "__main__":
    print("Medições normalizadas:", atualizar())
