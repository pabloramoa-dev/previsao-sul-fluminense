"""Confiança explícita adaptada do RJ; sem afirmar observações inexistentes."""
from datetime import datetime
from zoneinfo import ZoneInfo
import math
from .confidence import compute


def assess(data, reference=None):
    reference = reference or datetime.now(ZoneInfo('America/Sao_Paulo'))
    try:
        stamp = datetime.fromisoformat(data['gerado_em'])
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=ZoneInfo('America/Sao_Paulo'))
        age = (reference-stamp).total_seconds()/60
    except (KeyError, ValueError, TypeError):
        age = 1000000
    cities = data.get('cidades') or []
    valid = lambda x: isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
    if not cities or any(not all(valid(c.get(k)) for k in ('min','max','chuva_mm')) for c in cities):
        raise ValueError('Previsão incompleta: mínimas, máximas ou chuva ausentes')
    point = max(cities, key=lambda c:c['max'])
    model = {'max_c':point['max'], 'rain_probability_pct':point.get('prob_chuva')}
    report = compute(per_model={'open-meteo':model},age_minutes=age,freshness_ttl_minutes=120,
        previous_reference=None,current_reference=model,observed_status='not_collected',
        observation_agreement=None,spatial_fits=['medio']*len(cities))
    report['notes'].append('Uma fonte disponível; concordância entre modelos e observações não verificada.')
    if age < -5:
        raise ValueError('Horário da coleta está no futuro')
    if age>120:
        raise ValueError('Previsão vencida ou sem horário de coleta; coletar novamente')
    return report
