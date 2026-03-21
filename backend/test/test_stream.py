#!/usr/bin/env python
"""
Script de teste para o streaming SSE (Milestone 4).

Testa se os tokens aparecem progressivamente via SSE.
"""

import requests
import json
import sys

API_URL = "http://localhost:8000/api"

def test_streaming():
    """Testa o endpoint de streaming."""

    print("=" * 70)
    print("TESTE STREAMING SSE (Milestone 4)")
    print("=" * 70)

    # Usar conversa 1 (assumindo que existe)
    conversation_id = 1
    question = "Qual é o prazo do projeto?"

    print(f"\n1. Testando streaming para conversa {conversation_id}")
    print(f"   Pergunta: {question}\n")

    try:
        response = requests.post(
            f"{API_URL}/conversations/{conversation_id}/messages/stream/",
            json={"content": question},
            stream=True,
            headers={"Accept": "text/event-stream"},
            timeout=60,
        )

        if response.status_code != 200:
            print(f"! Erro HTTP {response.status_code}")
            print(f"  {response.text}")
            return False

        print("2. Lendo eventos SSE:\n")

        full_response = []
        event_count = 0

        for line in response.iter_lines():
            if not line:
                continue

            # SSE format: data: {json}
            if line.startswith(b"data: "):
                event_count += 1
                try:
                    json_str = line[6:].decode('utf-8')  # Remove "data: "
                    data = json.loads(json_str)

                    if "token" in data:
                        token = data["token"]
                        full_response.append(token)
                        # Print token without newline para simular streaming
                        print(token, end="", flush=True)

                    if "done" in data and data["done"]:
                        print("\n")
                        print(f"   Message ID: {data.get('message_id')}")
                        print(f"   User Message ID: {data.get('user_message_id')}")

                except json.JSONDecodeError as e:
                    print(f"\n! Erro ao parsear JSON: {e}")
                    print(f"  Linha: {line}")
                    continue

        print(f"\n3. Resumo:")
        print(f"   Total de eventos: {event_count}")
        print(f"   Total de tokens: {len(full_response)}")
        print(f"   Caracteres: {len(''.join(full_response))}")

        print("\n" + "=" * 70)
        print("TESTE STREAMING: SUCESSO!")
        print("=" * 70)
        return True

    except requests.exceptions.ConnectionError:
        print("! Erro: Django não está rodando em http://localhost:8000")
        print("  Execute: python manage.py runserver")
        return False
    except Exception as e:
        print(f"\n! Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_streaming()
    sys.exit(0 if success else 1)
