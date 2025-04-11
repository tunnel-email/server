import asyncio
from email.parser import BytesParser
from email.policy import default
from mailtunnel.snitun.server import sni
from mailtunnel.snitun.exceptions import ParseSNIError
from mailtunnel.database.routing_db import *
import logging


_logger = logging.getLogger(__name__)

class SMTPProxy:
    def __init__(self, dest_host, dest_port):
        self.dest_host = dest_host
        self.dest_port = dest_port


    async def send_cmd(self, writer, cmd):
        writer.write(f"{cmd}\r\n".encode("utf-8"))

        await writer.drain()


    async def get_response(self, reader):
        response = []

        while True:
            resp = await reader.readline()
            resp = resp.decode().strip()

            if not resp:
                break

            response.append(resp)

            if resp[3] == " ": # 220-... - continue; 220 ... - break
                break

        return response


    async def connect(self):
        self.remote_reader, self.remote_writer = await asyncio.open_connection(self.dest_host, self.dest_port)
        _logger.debug(f"Established proxy connection with {self.dest_host}:{self.dest_port}")
        
        # INIT SMTP connection
        init_line = await self.get_response(self.remote_reader)

        _logger.debug(f"Proxy endpoint {self.dest_host}:{self.dest_port} initial msg: {init_line}")

        await self.send_cmd(self.remote_writer, "HELO smtpproxy")
        
        resp1 = await self.get_response(self.remote_reader)

        _logger.debug(f"Proxy endpoint {self.dest_host}:{self.dest_port} asnwer on HELO: {resp1}")

        await self.send_cmd(self.remote_writer, "STARTTLS")

        resp2 = await self.get_response(self.remote_reader)

        _logger.debug(f"Proxy endpoint {self.dest_host}:{self.dest_port} asnwer on STARTTLS: {resp2}")


    async def send_to_endpoint(self, data):
        self.remote_writer.write(data)

        await self.remote_writer.drain()


    async def forward_traffic(self, reader, writer):
        # Forward data between two reader/writer pairs (client <-> remote).

        async def _pump(reader, writer):
            try:
                while True:
                    data = await reader.read(4096)
                    if not data:
                        break
                    writer.write(data)
                    await writer.drain()
            except asyncio.CancelledError:
                pass
            finally:
                writer.close()
        
        # Run bidirectional copy until one side closes
        task1 = asyncio.create_task(_pump(reader, self.remote_writer))
        task2 = asyncio.create_task(_pump(self.remote_reader, writer))

        _logger.debug(f"Started forwarding traffic to {self.dest_host}:{self.dest_port}")
        
        await asyncio.wait(
            [task1, task2],
            return_when=asyncio.FIRST_COMPLETED
        )

        task1.cancel()
        task2.cancel()


class SNIProxy:
    def __init__(self):
        pass

    async def tunnel(self, reader, writer):
        addr = writer.get_extra_info("peername")
        client_hello = await sni.payload_reader(reader)

        try:
            server_name = sni.parse_tls_sni(client_hello).lower().split(".")[0]
        except ParseSNIError:
            _logger.error(f"Unable to read SNI from {addr}")
            return

        _logger.debug(f"Received SNI: {server_name}")

        with RoutingDB() as r_db:
            tunnel_port = r_db.get_port_by_subdomain(server_name)

        _logger.debug(f"SNI: {server_name} from {addr}, ENDPOINT: {tunnel_port}")

        if tunnel_port:
            proxy = SMTPProxy("127.0.0.1", tunnel_port)

            _logger.debug(f"Trying to connect {tunnel_port}...")
            await proxy.connect()
            await proxy.send_to_endpoint(client_hello)

            await proxy.forward_traffic(reader, writer)

            _logger.info(f"Finished forwarding traffic from {addr}")


class SMTPServer:
    def __init__(self, host, port, sni_proxy: SNIProxy):
        self.host = host
        self.port = port
        self.sni_proxy = sni_proxy
    

    async def send_response(self, writer, response):
        writer.write(f"{response}\r\n".encode("utf-8"))

        await writer.drain()


    async def receive_data(self, reader):
        email_lines = []

        while True:
            line = await reader.readline()

            if line == b".\r\n" or line == b"":
                break
            if line == b"..\r\n":
                line = line[1:]

            email_lines.append(line)

        email_data = b"".join(email_lines)

        parser = BytesParser(policy=default)
        return parser.parsebytes(email_data)


    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        _logger.info(f"{addr} connected")

        await self.send_response(writer, "220 SMTP proxy")

        while True:
            try:
                data = await reader.readline()
            except ConnectionResetError:
                break
            message = data.decode().strip()

            if not message:
                break

            _logger.debug(f"Received message: {message}, len: {len(message)} from {addr}")

            if message.startswith("HELO"):
                await self.send_response(writer, "250 Hello")
            elif message.startswith("EHLO"):
                await self.send_response(writer, "250-Hello\r\n250 STARTTLS")
            elif message == "STARTTLS":
                await self.send_response(writer, "220 Ready to start TLS")

                await self.sni_proxy.tunnel(reader, writer)

                _logger.debug(f"Stopped answering SMTP from {addr}")
                return
            elif message == "QUIT":
                await self.send_response(writer, "221 Bye")
                break
                
            else:
                await self.send_response(writer, "500 Command not recognized")     

        writer.close()
        await writer.wait_closed()

        _logger.info(f"Closed connection for {addr}")

    
    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        _logger.info(f"Server info: {server!r}")

        async with server:
            await server.serve_forever()

