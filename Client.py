import errno
import socket
import random
import threading
import time
import struct
import select
from colors import colors
class Player:


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


        print(f"{colors.YELLOW}Client started, listening for offer requests...{colors.RESET}")
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
                            f"{colors.GREEN}Received offer from server at address {addr[0]}, attempting to connect...{colors.RESET}")
                        self.connect_to_server(addr[0], server_port)
            except struct.error as e:
                print(f"{colors.RED}Error unpacking data: {e}{colors.RESET}")

            except KeyboardInterrupt as k:
                print(f"{colors.RED}Client aborted connection: {k}{colors.RESET}")
                break






    def connect_to_server(self, server_ip, server_port):
        """Connect to the server using TCP."""

        self.server_ip = server_ip
        self.server_port = server_port
        self.stop_game = threading.Event()
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
            print(f"{colors.GREEN}Connected to {self.server_ip} on port {self.server_port}.{colors.RESET}")

            self.tcp_socket.sendall((self.player_name + '\n').encode())
            print(f"{colors.BLUE}you are player {self.player_name}, good luck:){colors.RESET}")

            self.game_loop()

        except Exception as e:
            print(f"{colors.RED}Error connecting to server: {e}{colors.RESET}")
            self.reconnect_to_server()
        finally:
            self.stop_game.set()
            self.tcp_socket.close()
            print(f"{colors.YELLOW}Socket closed. Ready to reconnect.{colors.RESET}")







    def game_loop(self):
        """Handle the game interactions over a TCP connection."""

        global input_allowed  # Use global variable for the input flag
        input_allowed = False  # Flag to control when input is allowed

        def user_input_thread():
            global input_allowed
            while not self.stop_game.is_set():
                if input_allowed:
                    try:
                        response = input()
                        if response.upper() in ['Y', 'T', '1']:
                            response = 'Y'
                        elif response.upper() in ['N', 'F', '0']:
                            response = 'N'
                        else:
                            print(f"{colors.RED}Invalid input. Please answer with Y/T/1 for True or N/F/0 for False..{colors.RESET}")
                            continue
                        print(f"{colors.BLUE}Your answer is: {response}{colors.RESET}")
                        self.tcp_socket.sendall(response.encode())

                    except:
                        if self.stop_game.is_set():
                            break  # If game over, exit the thread

        # Start the input thread but do not allow input yet
        input_thread = threading.Thread(target=user_input_thread)
        input_thread.start()

        try:
            while not self.stop_game.is_set():
                ready_to_read, _, _ = select.select([self.tcp_socket], [], [], 0.1)
                if self.tcp_socket in ready_to_read:
                    message = self.tcp_socket.recv(self.BUFFER_SIZE).decode().strip()

                    if message:
                        if '1' in message:
                            input_allowed = True  # Enable input when "1" is received
                        if ("Server disconnected, listening for offer requests..."  or "Resetting game") in message:
                            self.stop_game.set()
                            break

                        print(f"{colors.MAGENTA}{message}{colors.RESET}")
                        if "You are disqualified" in message:
                            continue
                        if "Game over" in message or "You win" in message:
                            self.stop_game.set()
                            print(f"{colors.YELLOW}Server disconnected, listening for offer requests....{colors.RESET}")
                            break
        except Exception as e:
            print(f"{colors.RED}Error during game: {e}.{colors.RESET}")
            if isinstance(e, socket.error) and e.errno in [errno.ECONNRESET, errno.ECONNABORTED, errno.EPIPE]:
                self.reconnect_to_server()
        finally:
            self.stop_game.set()  # Signal input thread to stop
            input_thread.join(timeout=1)  # Use a timeout to avoid being stuck here




    def reconnect_to_server(self):
        '''
        handle the case that the server is disconnected, trying to reconnect to the server
        '''

        print(f"{colors.YELLOW}Attempting to reconnect to the server...{colors.RESET}")

        for attempt in range(3):  # Try to reconnect 3 times
            try:
                # Close the previous socket if it's open
                if self.tcp_socket is not None:
                    self.tcp_socket.close()
                # Re-initialize socket
                self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_socket.connect((self.server_ip, self.server_port))
                print(f"{colors.GREEN}Reconnected to the server on attempt {attempt + 1}.{colors.RESET}")
                self.tcp_socket.sendall((self.player_name + '\n').encode())
                print(f"{colors.BLUE}you are player {self.player_name}, good luck:){colors.RESET}")
                self.game_loop()  # Resume the game loop
                return  # Exit the function upon successful reconnection
            except socket.error as e:
                print(f"{colors.RED}Reconnection attempt {attempt + 1} failed: {e}{colors.RESET}")
                time.sleep(3)  # Wait for 3 seconds before retrying

        # If reconnection failed after 3 attempts, handle accordingly
        print(f"{colors.RED}Failed to reconnect after 3 attempts.{colors.RESET}")
        # Close the socket and clean up before listening for offers again
        if self.tcp_socket is not None:
            self.tcp_socket.close()
        self.listen_for_offers()  # Go back to listening for new offers





    def run(self):
        """Run the main loop to continuously listen for offers."""
        while True:
            self.listen_for_offers()
            time.sleep(1)  # Delay to allow socket closure and cleanup


# Create and start the client
if __name__ == '__main__':
    client = Player()
    client.run()
