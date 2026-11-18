"""Coleta real do Sul Fluminense e gera relatório de candidatos (NÃO publica)."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.main import _coletar
from src.eventos_bruscos import detectar_eventos


def montar(cidades):
    resultado = []
    for c in cidades:
        series = c.horarias
        horas = series.get("time", [])
        linhas = []
        campos = {"precipitation_mm": "precipitation",
                  "temperature_c": "temperature_2m",
                  "wind_gust_kmh": "wind_gusts_10m",
                  "weather_code": "weathercode"}
        for i, hora in enumerate(horas):
            registro = {"time": hora}
            for destino, origem in campos.items():
                valores = series.get(origem) or []
                registro[destino] = valores[i] if i < len(valores) else None
            linhas.append(registro)
        resultado.append({"nome": c.nome, "hourly": linhas})
    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default="saida/eventos_bruscos/relatorio.json")
    args = parser.parse_args()
    cidades, _ = _coletar()
    eventos = detectar_eventos(montar(cidades))
    out = Path(args.saida)
    out.parent.mkdir(parents=True, exist_ok=True)
    relatorio = {"emitido_em": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
                 "cidades_consultadas": len(cidades), "quantidade": len(eventos),
                 "eventos": eventos, "publicacao_automatica": False,
                 "observacao": "Previsões não são avisos oficiais nem chuva observada."}
    out.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"eventos_candidatos": len(eventos), "arquivo": str(out)}))


if __name__ == "__main__":
    main()
