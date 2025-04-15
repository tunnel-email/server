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

        self.remote_reader = None
        self.remote_writer = None

    async def send_cmd(self, cmd):
        await self.send_to_endpoint(f"{cmd}\r\n".encode("utf-8"))
        _logger.debug(f"Cmd sent successfuly")


    async def get_response(self, reader):
        response = []

        try:
            while not reader.at_eof():
                try:
                    resp = await asyncio.wait_for(reader.readline(), timeout=5.0)
                    resp_str = resp.decode().strip()

                    if not resp_str:
                        break

                    response.append(resp_str)

                    # 220-... - continue; 220 ... - break
                    if resp_str and len(resp_str) > 3 and resp_str[3] == " ": 
                        break
                except asyncio.TimeoutError:
                    _logger.warning(f"Timeout in get_response {self.dest_host}:{self.dest_port}")
                    break
        except (ConnectionResetError, ConnectionError) as e:
            _logger.warning(f"Connection problem in get_response: {e}")

        return response


    async def connect(self, max_attempts = 3):
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            try:
                _logger.debug(f"[Attempt {attempts}] connecting to {self.dest_host}:{self.dest_port}...")
                self.remote_reader, self.remote_writer = await asyncio.open_connection(
                    self.dest_host, self.dest_port
                )

                _logger.debug(f"Connection established with {self.dest_host}:{self.dest_port}")

                init_line = await self.get_response(self.remote_reader)

                _logger.debug(f"Initial message: {init_line}")

                if not init_line:
                    raise ConnectionError("No initial greeting from endpoint.")

                # No HELO/EHLO. STARTTLS first

                await self.send_cmd("STARTTLS")
                _logger.debug("STARTTLS command sent, waiting for response...")

                resp_starttls = await asyncio.wait_for(self.get_response(self.remote_reader), timeout=5.0)
                _logger.debug(f"STARTTLS response: {resp_starttls}")

                if not resp_starttls or not any(line.startswith("220") or "Ready" in line for line in resp_starttls):
                    raise asyncio.TimeoutError("STARTTLS response not received properly.")

                _logger.info("STARTTLS command acknowledged")
                return 

            except (asyncio.TimeoutError, ConnectionError) as e:
                _logger.warning(f"[Attempt {attempts}] error during connection: {e}. Reconnecting...")

                if self.remote_writer is not None:
                    self.remote_writer.close()

                    try:
                        await self.remote_writer.wait_closed()
                    except Exception:
                        pass

                await asyncio.sleep(1)

        raise ConnectionError(f"Unable to connect to {self.dest_host}:{self.dest_port} after {max_attempts} attempts.")


    async def send_to_endpoint(self, data):
        try:
            self.remote_writer.write(data)

            await asyncio.wait_for(self.remote_writer.drain(), timeout=10.0) # timeout 
        except (ConnectionResetError, ConnectionError, asyncio.TimeoutError) as e:
            _logger.warning(f"Error in send_to_endpoint {self.dest_host}:{self.dest_port}: {e}")

            raise # re-raise


    async def forward_traffic(self, reader, writer):
        # forward data between two reader/writer pairs

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
        
        # bidirectional copy until one side closes
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

            try:
                await proxy.connect()
            except ConnectionError:
                return

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

