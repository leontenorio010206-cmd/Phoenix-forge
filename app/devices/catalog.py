import json
from pathlib import Path


def validate_profile(profile):
    required = ("id", "name", "manufacturer", "family", "scope", "resources", "restrictions", "sources", "compatibility")
    if any(key not in profile for key in required):
        raise ValueError("Perfil incompleto")
    if profile["scope"] not in ("device", "family"):
        raise ValueError("Alcance de perfil inválido")
    if not profile["sources"] or not all(url.startswith("https://") for url in profile["sources"]):
        raise ValueError("Un perfil requiere fuentes técnicas")
    c = profile["compatibility"]
    for key in ("informational", "logical_simulation", "synthesis_verified", "programming_verified"):
        if type(c.get(key)) is not bool:
            raise ValueError("Estado de compatibilidad inválido")
    if (c["synthesis_verified"] or c["programming_verified"]) and not profile.get("verification_evidence"):
        raise ValueError("Se requiere evidencia de verificación")
    if profile["scope"] == "family" and profile.get("numeric_resources"):
        raise ValueError("No asigne recursos de un chip a una familia general")
    return profile


def load_profiles():
    path = Path(__file__).with_name("profiles.json")
    profiles = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for profile in profiles:
        validate_profile(profile)
        if profile["id"] in result:
            raise ValueError("ID de dispositivo duplicado")
        result[profile["id"]] = profile
    return result

