from .rag_graph import run_query


def main() -> None:
    print("=== RAG Customer Support Assistant (type 'quit' to exit) ===")
    while True:
        query = input("User: ").strip()
        if query.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        result = run_query(query)
        print(f"Bot: {result['answer']}")
        print(
            f"   route={result['route']} | confidence={result['confidence']} | intent={result['intent']}"
        )
        if result["hitl_ticket_id"]:
            print(f"   HITL Ticket: {result['hitl_ticket_id']}")


if __name__ == "__main__":
    main()
