#!/usr/bin/env python3
"""Local development script for testing the Service Desk agent."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.graph.service_desk_graph import invoke_service_desk


def main():
    """Run interactive Service Desk session."""
    print("=" * 60)
    print("Service Desk Multi-Agent System - Local Testing")
    print("=" * 60)
    print("Escribe tu consulta y presiona Enter.")
    print("Escribe 'exit' o 'quit' para salir.")
    print("=" * 60)
    print()

    session_id = "local-test-session"

    while True:
        try:
            user_input = input("Tú: ").strip()

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "salir"}:
                print("\n¡Hasta luego!")
                break

            print("\nProcesando...")
            result = invoke_service_desk(user_input, session_id)

            print(f"\n[Clasificación: {result.get('classification', 'unknown')}]")
            print(f"[Confianza: {result.get('confidence_score', 0):.2f}]")
            print(f"[Agentes: {' -> '.join(result.get('agent_trace', []))}]")

            if result.get("needs_human_escalation"):
                print("[⚠️ Caso marcado para escalamiento]")

            print(f"\nAgente: {result.get('response', 'Sin respuesta')}")
            print()

        except KeyboardInterrupt:
            print("\n\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Intenta de nuevo.\n")


if __name__ == "__main__":
    main()
