# PYTHON_ARGCOMPLETE_OK
"""
k8co.py

Script de consola para cambiar rapidamente el contexto activo de Kubernetes.

El flujo general es:
1. Leer los argumentos de busqueda desde la terminal.
2. Consultar los contextos disponibles con kubectl.
3. Filtrar contextos por cuenta/proyecto y, opcionalmente, por ambiente.
4. Si hay varias coincidencias, mostrar un menu interactivo.
5. Ejecutar `kubectl config use-context` con el contexto seleccionado.
"""

import argparse
import subprocess
import sys
from collections.abc import Callable
from difflib import get_close_matches

import argcomplete
from simple_term_menu import TerminalMenu

def cuenta_completer(prefix: str, parsed_args: argparse.Namespace, **_kwargs: object) -> list[str]:
    contextos = obtener_contextos()
    cuentas = extraer_texto_del_contexto(contextos, 0)
    prefix = prefix.lower()
    return sorted(cuenta for cuenta in cuentas if cuenta.startswith(prefix))


def ambiente_completer(prefix: str, parsed_args: argparse.Namespace, **_kwargs: object) -> list[str]:
    contextos = obtener_contextos()
    cuenta = getattr(parsed_args, "account", None)

    if not cuenta:
        return []

    contextos_cuenta = filtrar_contextos(contextos, cuenta)
    ambientes = extraer_texto_del_contexto(contextos_cuenta, 1)
    prefix = prefix.lower()

    return sorted(ambiente for ambiente in ambientes if ambiente.startswith(prefix))

def obtener_argumentos() -> argparse.Namespace:
    """Define y devuelve los argumentos recibidos por linea de comandos."""
    texto_ayuda = """

        INFO
        - Este comando NO requiere parámetros con guiones (como --cuenta o --ambiente).
        - Los valores se pasan directamente en orden como variables posicionales.

        EJEMPLOS
            k8co alpha
            k8co alpha prod
            k8co beta dev
            k8co local

        NOTAS
            - La cuenta es la primera parte del contexto: alpha-prod -> alpha.
            - El ambiente es opcional: alpha-prod -> prod.
            - Si hay varias coincidencias, se muestra un menú.
            - Si escribís algo parecido, k8co puede sugerir una corrección.
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="k8co <cuenta> [ambiente]",
        description="Herramienta para Cambio de Contexto en Kubernetes",
        epilog=texto_ayuda + "Y asi es como cambias de contexto rapidamente en k8s",
    )

    argumento_cuenta =parser.add_argument("account", type=str.lower, help="Proyecto al que te deseas conectar (DEBE IR PRIMERO)")
    argumento_ambiente =parser.add_argument("ambiente",type=str.lower,nargs="?",help="Ambiente al que te deseas conectar (OPCIONAL, DEBE IR SEGUNDO)")

    argumento_cuenta.completer = cuenta_completer # type: ignore[attr-defined]
    argumento_ambiente.completer = ambiente_completer # type: ignore[attr-defined]
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


def obtener_contextos() -> list[str]:
    """Obtiene desde kubectl la lista de contextos configurados localmente."""
    comando_contextos = subprocess.run(
        ["kubectl", "config", "get-contexts", "-o", "name"],
        capture_output=True,
        text=True,
    )
    if comando_contextos.returncode != 0:
        print("Error obteniendo contextos de kubectl")
        sys.exit(1)
    return comando_contextos.stdout.splitlines()

def sugerir_coincidencia(valor_usuario: str, opciones_validas: list[str]) -> str | None:
    """Sugiere una coincidencia cercana si el valor del usuario no es valido. basicamente hace FUZZY"""
    sugerencia = get_close_matches(valor_usuario, opciones_validas, n=1, cutoff=0.6)
    return sugerencia[0] if sugerencia else None

def extraer_texto_del_contexto(contextos: list[str], que_busca: int) -> list[str]:
    """Extrae partes únicas de los contextos según su posición."""
    lista_cuentas = set()
    for contexto in contextos:
        if len(contexto.split("-")) > que_busca:
            cuenta = contexto.split("-")[que_busca]
            lista_cuentas.add(cuenta)
    return list(lista_cuentas)

def filtrar_contextos(lista_contextos: list[str], palabra_a_buscar: str) -> list[str]:
    """Filtra contextos por una palabra clave."""
    return [contexto for contexto in lista_contextos if palabra_a_buscar in contexto]


def confirmar_sugerencia(sugerencia: str, comparacion: str) -> bool:
    """Pregunta al usuario si la sugerencia es correcta."""
    if sugerencia == comparacion:
        return True
    else:
        try:
            print(f"¿No se encontró '{comparacion}'? Se sugiere '{sugerencia}'.")
            respuesta = input(f"¿Querías decir '{sugerencia}'? (S/n): ").strip().lower()
            return respuesta == "s"
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
            sys.exit(1)

def resolver_busqueda_contextos(lista_contextos: list[str], cuenta: str, ambiente: str | None = None, confirmar: Callable[[str, str], bool] = confirmar_sugerencia) -> list[str]:
    """Filtra contextos por cuenta y, si existe, tambien por ambiente."""
    cuenta = cuenta.lower()
    ambiente = ambiente.lower() if ambiente else None
    lista_cuentas_disponibles = extraer_texto_del_contexto(lista_contextos,0)
    cuenta_a_buscar = sugerir_coincidencia(cuenta, lista_cuentas_disponibles)
    if not cuenta_a_buscar:
        return []
    else:
        if confirmar(cuenta_a_buscar, cuenta):
            lista_cuentas_filtrados = filtrar_contextos(lista_contextos, cuenta_a_buscar)
        else:
            lista_cuentas_filtrados = filtrar_contextos(lista_contextos, cuenta)

        if not ambiente:
            return lista_cuentas_filtrados
        else:
            lista_ambientes_disponibles = extraer_texto_del_contexto(lista_cuentas_filtrados,1)
            ambiente_a_buscar = sugerir_coincidencia(ambiente,lista_ambientes_disponibles)
            if ambiente_a_buscar and confirmar(ambiente_a_buscar, ambiente):
                return filtrar_contextos(lista_cuentas_filtrados, ambiente_a_buscar)
            else:
                return lista_cuentas_filtrados


def seleccionar_contexto(contextos_encontrados: list[str]) -> str:
    """Devuelve el contexto final: automatico si hay uno, interactivo si hay varios."""
    if len(contextos_encontrados) == 0:
        print(
            "No se encontraron contextos que coincidan con los criterios "
            "proporcionados."
        )
        sys.exit(1)
    elif len(contextos_encontrados) == 1:
        return contextos_encontrados[0]
    else:
        # Se muestra una lista numerada para que el usuario pueda elegir visualmente.
        contextos_enumerados = [
            f"[{index + 1}] {context}"
            for index, context in enumerate(contextos_encontrados)
        ]
        menu_interactivo = TerminalMenu(
            contextos_enumerados,
            title="Selecciona el contexto al que deseas conectarte:",
            menu_cursor=("👉"),
            menu_highlight_style=("fg_green", "bold"),
            show_search_hint=True,
        )
        indice_seleccionado = menu_interactivo.show()
        if indice_seleccionado is None:
            print("No se selecciono ningun contexto.")
            sys.exit(1)
        if not isinstance(indice_seleccionado, int):
            print("Seleccion invalida. Por favor, elige un numero de la lista.")
            sys.exit(1)
        opcion_seleccionada = contextos_encontrados[indice_seleccionado]
        return opcion_seleccionada


def establecer_contexto(contexto: str) -> None:
    """Cambia el contexto activo de kubectl al contexto seleccionado."""
    resultado = subprocess.run(
        ["kubectl", "config", "use-context", contexto],
        capture_output=True,
        text=True,
    )
    codigo_salida = resultado.returncode

    if codigo_salida != 0:
        print(f"Error al cambiar el contexto: {resultado.stderr}")
        sys.exit(codigo_salida)
    else:
        print(f"Contexto cambiado exitosamente a: {contexto}")


def main() -> None:
    # Punto de entrada del script cuando se ejecuta como programa.
    argumentos = obtener_argumentos()
    contextos = obtener_contextos()
    coincidencias = resolver_busqueda_contextos(contextos, argumentos.account, argumentos.ambiente)
    contexto_seleccionado = seleccionar_contexto(coincidencias)
    print(f"Contexto seleccionado: {contexto_seleccionado}")
    establecer_contexto(contexto_seleccionado)

if __name__ == "__main__":
    main()
