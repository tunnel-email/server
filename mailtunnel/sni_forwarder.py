from mailtunnel.forwarder.objects import *
import asyncio
import logging


async def forwarder():
    sni_proxy = SNIProxy()
    smtp_server = SMTPServer("0.0.0.0", 25, sni_proxy)

    await smtp_server.start()

def main():
    asyncio.run(forwarder())

if __name__ == "__main__":
    main()
