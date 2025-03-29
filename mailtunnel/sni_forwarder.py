from mailtunnel.forwarder.objects import *
import asyncio
import logging


# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    sni_proxy = SNIProxy()
    smtp_server = SMTPServer("0.0.0.0", 25, sni_proxy)

    await smtp_server.start()

asyncio.run(main())
