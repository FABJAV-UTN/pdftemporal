"""
Crea de una sola vez los issues de la Parte 1 de ISSUES_KANBAN.md en GitHub,
con labels, asignados y (opcional) agregados al GitHub Project.

Requisitos:
  - GitHub CLI instalado: https://cli.github.com
  - Sesión iniciada con permiso de projects:
        gh auth login
        gh auth refresh -s project

Uso:
  1. Completar la CONFIGURACIÓN de abajo.
  2. Probar sin crear nada:      python3 crear_issues.py
  3. Crear de verdad:            python3 crear_issues.py --crear

Si se corta a la mitad, se puede volver a correr: los issues que ya existen
(mismo título) no se duplican.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------------ #
# CONFIGURACIÓN — completar antes de correr con --crear
# ------------------------------------------------------------------ #

REPO = "OWNER/REPO"            # ej: "fabiojflores/pdf-extractext"

# Usuarios de GitHub de cada integrante (sin @).
USUARIOS = {
    "Fabio": "USUARIO_FABIO",
    "Luciana": "USUARIO_LUCIANA",
    "Celina": "USUARIO_CELINA",
}

# GitHub Project donde agregar los issues. Dejar PROJECT_NUMBER = None para no agregarlos.
# El número sale de la URL: github.com/users/<owner>/projects/<NUMERO>
#                       o: github.com/orgs/<owner>/projects/<NUMERO>
PROJECT_OWNER = "OWNER"
PROJECT_NUMBER = None

ARCHIVO_MD = Path(__file__).with_name("ISSUES_KANBAN.md")

COLORES_LABELS = {
    "bug": "d73a4a",
    "clean-code": "0e8a16",
    "tdd": "1d76db",
    "12-factor": "5319e7",
    "infra": "fbca04",
    "docs": "0075ca",
    "rendimiento": "e99695",
    "solid": "006b75",
}

# ------------------------------------------------------------------ #
# Lectura del markdown
# ------------------------------------------------------------------ #

TITULO_ISSUE = re.compile(r"^### Issue (\d+) — (.+)$")
GRUPO_PERSONA = re.compile(r"^## (Fabio|Luciana|Celina) — ")
LABEL = re.compile(r"`([a-z0-9-]+)`")


def leer_issues(md: str) -> list[dict]:
    """Devuelve los issues de la Parte 1 (todo lo que está antes de 'Orden recomendado')."""
    parte1 = md.split("# Parte 1 — Issues", 1)[1].split("## Orden recomendado", 1)[0]

    issues: list[dict] = []
    persona_del_grupo = None
    actual = None

    for linea in parte1.splitlines():
        grupo = GRUPO_PERSONA.match(linea)
        if grupo:
            persona_del_grupo = grupo.group(1)

        titulo = TITULO_ISSUE.match(linea)
        if titulo:
            actual = _nuevo_issue(int(titulo.group(1)), titulo.group(2), persona_del_grupo)
            issues.append(actual)
            continue

        if linea.startswith("## ") or linea.strip() == "---":
            actual = None
            continue

        if actual is not None:
            actual["cuerpo"].append(linea)

    for issue in issues:
        issue["cuerpo"] = "\n".join(issue["cuerpo"]).strip()
    return issues


def _nuevo_issue(numero: int, encabezado: str, persona_del_grupo: str | None) -> dict:
    # Encabezado: "Título · Persona · `label` `label`"  o  "Título · `label`"
    partes = [p.strip() for p in encabezado.split(" · ")]
    titulo = partes[0]
    persona = next((p for p in partes[1:] if p in USUARIOS), persona_del_grupo)
    labels = LABEL.findall(" ".join(partes[1:]))
    return {"n": numero, "titulo": titulo, "persona": persona, "labels": labels, "cuerpo": []}


def con_referencias(cuerpo: str, numeros_reales: dict[int, int]) -> str:
    """Reemplaza 'issue 13' / 'issues 10 y 13' por '#<número real en GitHub>'."""

    def reemplazar(match: re.Match) -> str:
        n = int(match.group(0))
        return f"#{numeros_reales[n]}" if n in numeros_reales else match.group(0)

    def en_frase(match: re.Match) -> str:
        return re.sub(r"\d+", reemplazar, match.group(0))

    return re.sub(r"[Ii]ssues? \d+(?:(?:, | y )\d+)*", en_frase, cuerpo)


# ------------------------------------------------------------------ #
# GitHub CLI
# ------------------------------------------------------------------ #

def gh(*args: str) -> str:
    resultado = subprocess.run(["gh", *args], capture_output=True, text=True)
    if resultado.returncode != 0:
        sys.exit(f"Error en: gh {' '.join(args)}\n{resultado.stderr}")
    return resultado.stdout.strip()


def issues_existentes() -> dict[str, int]:
    salida = gh("issue", "list", "--repo", REPO, "--state", "all", "--limit", "500", "--json", "number,title")
    return {i["title"]: i["number"] for i in json.loads(salida)}


def crear_labels(issues: list[dict]) -> None:
    for label in sorted({l for i in issues for l in i["labels"]}):
        color = COLORES_LABELS.get(label, "ededed")
        gh("label", "create", label, "--repo", REPO, "--color", color, "--force")
        print(f"  label {label}")


def crear_issue(issue: dict) -> int:
    args = ["issue", "create", "--repo", REPO, "--title", issue["titulo"], "--body", issue["cuerpo"]]
    for label in issue["labels"]:
        args += ["--label", label]
    if issue["persona"]:
        args += ["--assignee", USUARIOS[issue["persona"]]]
    url = gh(*args)
    if PROJECT_NUMBER is not None:
        gh("project", "item-add", str(PROJECT_NUMBER), "--owner", PROJECT_OWNER, "--url", url)
    return int(url.rstrip("/").split("/")[-1])


# ------------------------------------------------------------------ #
# Programa
# ------------------------------------------------------------------ #

def validar_configuracion() -> None:
    placeholders = {"OWNER/REPO", "OWNER", "USUARIO_FABIO", "USUARIO_LUCIANA", "USUARIO_CELINA"}
    valores = [REPO, *USUARIOS.values()] + ([PROJECT_OWNER] if PROJECT_NUMBER is not None else [])
    faltan = [v for v in valores if v in placeholders]
    if faltan:
        sys.exit(f"Completá la CONFIGURACIÓN al principio del script. Falta: {', '.join(faltan)}")


def main() -> None:
    crear = "--crear" in sys.argv
    issues = leer_issues(ARCHIVO_MD.read_text(encoding="utf-8"))

    if not crear:
        print(f"Modo prueba: se crearían {len(issues)} issues. Para crearlos: python3 crear_issues.py --crear\n")
        for i in issues:
            print(f"#{i['n']:>2}  [{i['persona'] or '-':<7}] {i['titulo']}  {i['labels']}")
        return

    validar_configuracion()
    existentes = issues_existentes()

    print("Labels:")
    crear_labels(issues)

    print("Issues:")
    numeros_reales: dict[int, int] = {}
    for issue in issues:
        if issue["titulo"] in existentes:
            numeros_reales[issue["n"]] = existentes[issue["titulo"]]
            print(f"  ya existe  #{numeros_reales[issue['n']]}  {issue['titulo']}")
            continue
        numeros_reales[issue["n"]] = crear_issue(issue)
        print(f"  creado     #{numeros_reales[issue['n']]}  {issue['titulo']}")

    # Segunda pasada: las dependencias ("Depende de: issue 13") pasan a ser links (#número real).
    print("Enlazando dependencias:")
    for issue in issues:
        cuerpo = con_referencias(issue["cuerpo"], numeros_reales)
        if cuerpo != issue["cuerpo"]:
            gh("issue", "edit", str(numeros_reales[issue["n"]]), "--repo", REPO, "--body", cuerpo)
            print(f"  #{numeros_reales[issue['n']]}")

    print("\nListo.")


if __name__ == "__main__":
    main()
