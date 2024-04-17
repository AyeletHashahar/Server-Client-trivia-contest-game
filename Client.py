import socket
import random
import threading
import time
import select
import struct
import sys
import select

class Player:

    ANSI_RED = '\033[31m'
    ANSI_GREEN = '\033[32m'
    ANSI_YELLOW = '\033[33m'
    ANSI_BLUE = '\033[34m'
    ANSI_MAGENTA = '\033[35m'
    ANSI_CYAN = '\033[36m'
    ANSI_RESET = '\033[0m'

    disney_characters = [
        "Mickey Mouse", "Minnie Mouse", "Donald Duck", "Goofy", "Pluto",
        "Simba", "Mufasa", "Nala", "Scar", "Timon", "Pumbaa",
        "Ariel", "Ursula", "Flounder", "Sebastian", "King Triton",
        "Elsa", "Anna", "Olaf", "Kristoff", "Sven",
        "Aladdin", "Jasmine", "Genie", "Jafar", "Iago",
        "Cinderella", "Prince Charming", "Fairy Godmother", "Lady Tremaine",
        "Belle", "Beast", "Gaston", "Lumière", "Cogsworth",
        "Mulan", "Shang", "Mushu", "Shan Yu",
        "Pocahontas", "John Smith", "Meeko", "Governor Ratcliffe",
        "Snow White", "The Evil Queen", "Prince", "Doc", "Grumpy", "Sleepy", "Sneezy", "Happy", "Bashful", "Dopey",
        "Woody", "Buzz Lightyear", "Jessie", "Bo Peep", "Forky",
        "Moana", "Maui", "Heihei",
        "Rapunzel", "Flynn Rider", "Mother Gothel",
        "Merida", "Queen Elinor", "King Fergus",
        "Hercules", "Megara", "Hades",
        "Tiana", "Prince Naveen", "Dr. Facilier",
        "Alice", "The Mad Hatter", "Queen of Hearts",
        "Tarzan", "Jane Porter", "Clayton",
        "Peter Pan", "Wendy", "Captain Hook",
        "Quasimodo", "Esmeralda", "Judge Claude Frollo"
    ]

    def __init__(self, udp_port=13117, magic_cookie=0xabcddcba, offer_message_type=0x2, buffer_size=1024):
        self.udp_port = udp_port
        self.magic_cookie = magic_cookie
        self.offer_message_type = offer_message_type
        self.server_ip = None
        self.server_port = None
        self.BUFFER_SIZE = buffer_size
        self.player_name = random.choice(self.disney_characters)
        self.stop_game = None
        self.tcp_socket = None

    def listen_for_offers(self):
        """Listen for offer messages via UDP broadcast."""
        print(f"{self.ANSI_YELLOW}Client started, listening for offer requests...{self.ANSI_RESET}")
        # Creates a UDP socket for listening to broadcast messages.
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Configures the socket to allow multiple applications to listen on the same port (SO_REUSEPORT) and to enable
        # broadcast packets (SO_BROADCAST).
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Binds the socket to the specified UDP port for all interfaces.
        client_socket.bind(("", self.udp_port))

        # Enters an infinite loop, waiting to receive data. recvfrom returns the data and the address of the sender.
        while True:
            data, addr = client_socket.recvfrom(self.BUFFER_SIZE)
            # If data is received, it unpacks the first 7 bytes into magic_cookie (4 bytes, integer), message_type (1 byte,
            # byte), and server_port (2 bytes, unsigned short).
            try:
                if data:
                    magic_cookie, message_type, server_name, server_port = struct.unpack('!Ib32sH', data)
                    # Checks if the received message starts with the expected MAGIC_COOKIE and MESSAGE_TYPE.
                    if magic_cookie == self.magic_cookie and message_type == self.offer_message_type:
                        print(
                            f"{self.ANSI_GREEN}Received offer from server at address {addr[0]}, attempting to connect...{self.ANSI_RESET}")
                        self.connect_to_server(addr[0], server_port)
            except struct.error as e:
                print(f"{self.ANSI_RED}Error unpacking data: {e}{self.ANSI_RESET}")

            except KeyboardInterrupt as k:
                print(f"{self.ANSI_RED}Client aborted connection: {k}{self.ANSI_RESET}")
                break

    def connect_to_server(self, server_ip, server_port):
        """Connect to the server using TCP."""
        self.server_ip = server_ip
        self.server_port = server_port
        self.stop_game = threading.Event()
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
            print(f"{self.ANSI_GREEN}Connected to {self.server_ip} on port {self.server_port}.{self.ANSI_RESET}")
            self.tcp_socket.sendall((self.player_name + '\n').encode())
            print(f"{self.ANSI_BLUE}you are player {self.player_name}, good luck:){self.ANSI_RESET}")
            self.game_loop()
        except Exception as e:
            print(f"{self.ANSI_RED}Error connecting to server: {e}{self.ANSI_RESET}")
        finally:
            self.stop_game.set()
            self.tcp_socket.close()
            print(f"{self.ANSI_YELLOW}Socket closed. Ready to reconnect.{self.ANSI_RESET}")

    def game_loop(self):
        """Handle the game interactions over a TCP connection."""
        # stop_game = threading.Event()

        def user_input_thread():
            while not self.stop_game.is_set():
                try:
                    response = input()
                    if response.upper() in ['Y', 'T', '1']:
                        response = 'Y'
                    elif response.upper() in ['N', 'F', '0']:
                        response = 'N'
                    else:
                        print(f"{self.ANSI_RED}Invalid input. Please answer with Y/T/1 for True or N/F/0 for False..{self.ANSI_RESET}")
                        continue
                    print(f"{self.ANSI_BLUE}Your answer is: {response}.{self.ANSI_RESET}")
                    self.tcp_socket.sendall(response.encode())

                except Exception as e:
                    if self.stop_game.is_set():
                        break  # If game over, exit the thread

        # Start the input thread
        input_thread = threading.Thread(target=user_input_thread)
        input_thread.start()

        try:
            while not self.stop_game.is_set():
                ready_to_read, _, _ = select.select([self.tcp_socket], [], [], 0.1)
                if self.tcp_socket in ready_to_read:
                    message = self.tcp_socket.recv(self.BUFFER_SIZE).decode().strip()

                    if message:
                        if "Server disconnected, listening for offer requests..." in message:
                            self.stop_game.set()
                            break
                        if "disconnected from the game" in message:
                            print(f"{self.ANSI_RED}{message}{self.ANSI_RESET}")
                        else:
                            print(f"{self.ANSI_MAGENTA}{message}{self.ANSI_RESET}")
                            if "You are disqualified" in message:
                                continue
                            if "Game over" in message or "You win" in message:
                                self.stop_game.set()
                                print(f"{self.ANSI_YELLOW}Server disconnected, listening for offer requests....{self.ANSI_RESET}")
                                break
        except:
            print(f"{self.ANSI_RED}The server disconnected{self.ANSI_RESET}")
            self.tcp_socket.close()
            self.listen_for_offers()

        finally:
            self.stop_game.set()  # Signal input thread to stop
            input_thread.join(timeout=1)  # Use a timeout to avoid being stuck here

    def run(self):
        """Run the main loop to continuously listen for offers."""
        while True:
            self.listen_for_offers()
            time.sleep(1)  # Delay to allow socket closure and cleanup


