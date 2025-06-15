import asyncio
from scanner.server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Servidor interrompido pelo usuário.")
