from k8co.cli import resolver_busqueda_contextos
from k8co.cli import extraer_texto_del_contexto

def confirmar_no(sugerencia, comparacion):
    return False
def confirmar_si(sugerencia, comparacion):
    return True

def test_buscar_sin_ambiente():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]
    resultado_esperado = ["alpha-prod", "alpha-dev"]
    resultado = resolver_busqueda_contextos(contextos_fake, "alpha")
    assert resultado == resultado_esperado, f"Resultado esperado: {resultado_esperado}, Resultado obtenido: {resultado}"

def test_buscar_con_ambiente_correcto():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]
    resultado_esperado = ["alpha-dev"]
    resultado = resolver_busqueda_contextos(contextos_fake, "alpha", "dev")
    assert resultado == resultado_esperado, f"Resultado esperado: {resultado_esperado}, Resultado obtenido: {resultado}"

def test_buscar_con_ambiente_incorrecto():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]
    resultado_esperado = ["alpha-prod", "alpha-dev"]
    resultado = resolver_busqueda_contextos(contextos_fake, "alpha", "arpa")
    assert resultado == resultado_esperado, f"Resultado esperado: {resultado_esperado}, Resultado obtenido: {resultado}"

def test_buscar_con_account_incorrecto():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]
    resultado_esperado = []
    resultado = resolver_busqueda_contextos(contextos_fake, "gamma")
    assert resultado == resultado_esperado, f"Resultado esperado: {resultado_esperado}, Resultado obtenido: {resultado}"

def test_buscar_con_account_incorrecto_ambiente_correcto():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]
    resultado_esperado = ["alpha-dev"]
    resultado = resolver_busqueda_contextos(contextos_fake, "alhpa", "dev", confirmar=confirmar_si)
    assert resultado == resultado_esperado, f"Resultado esperado: {resultado_esperado}, Resultado obtenido: {resultado}"

def test_account_con_typo_y_usuario_acepta():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]

    resultado = resolver_busqueda_contextos(
        contextos_fake,
        "alhpa",
        confirmar=confirmar_si,
    )

    assert resultado == ["alpha-prod", "alpha-dev"]


def test_account_con_typo_y_usuario_rechaza():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]

    resultado = resolver_busqueda_contextos(
        contextos_fake,
        "alhpa",
        confirmar=confirmar_no,
    )

    assert resultado == []


def test_ambiente_con_typo_y_usuario_acepta():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]

    resultado = resolver_busqueda_contextos(
        contextos_fake,
        "alpha",
        "prd",
        confirmar=confirmar_si,
    )

    assert resultado == ["alpha-prod"]


def test_ambiente_con_typo_y_usuario_rechaza():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]

    resultado = resolver_busqueda_contextos(
        contextos_fake,
        "alpha",
        "prd",
        confirmar=confirmar_no,
    )

    assert resultado == ["alpha-prod", "alpha-dev"]

def test_buscar_account_en_mayusculas():
    contextos_fake = ["alpha-prod", "alpha-dev", "beta-prod", "beta-dev"]
    resultado = resolver_busqueda_contextos(
        contextos_fake,
        "ALPHA",
    )
    assert resultado == ["alpha-prod", "alpha-dev"]


def test_buscar_account_con_contexto_sin_ambiente():
    contextos_fake = ["local", "alpha-prod", "alpha-dev"]
    resultado = resolver_busqueda_contextos(contextos_fake, "local")
    assert resultado == ["local"]


def test_buscar_account_sin_ambiente_pero_usuario_pasa_ambiente():
    contextos_fake = ["local", "alpha-prod", "alpha-dev"]
    resultado = resolver_busqueda_contextos(contextos_fake, "local", "preprod")
    assert resultado == ["local"]


def test_extraer_ambientes_ignora_contextos_sin_guion():
    contextos_fake = ["local", "alpha-prod", "alpha-dev"]
    resultado = extraer_texto_del_contexto(contextos_fake, 1)
    assert sorted(resultado) == ["dev", "prod"]


def test_extraer_cuentas_incluye_contexto_sin_guion():
    contextos_fake = ["local", "alpha-prod", "alpha-dev"]
    resultado = extraer_texto_del_contexto(contextos_fake, 0)
    assert sorted(resultado) == ["alpha", "local"]


def test_ambiente_en_mayusculas():
    contextos_fake = ["alpha-prod", "alpha-dev"]
    resultado = resolver_busqueda_contextos(
        contextos_fake,
        "alpha",
        "PROD",
    )
    assert resultado == ["alpha-prod"]
