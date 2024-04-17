import socket
import struct
import sys
import time
from threading import Thread, Lock
import threading
import random
from Statistic import GameStatistics

class Server:

    ANSI_RED = '\033[31m'
    ANSI_GREEN = '\033[32m'
    ANSI_YELLOW = '\033[33m'
    ANSI_BLUE = '\033[34m'
    ANSI_MAGENTA = '\033[35m'
    ANSI_CYAN = '\033[36m'
    ANSI_RESET = '\033[0m'

    disney_trivia_questions = [
        {"question": "Mickey Mouse was the first cartoon character to speak.", "is_true": False},
        {"question": "Elsa is considered a Disney Princess.", "is_true": False},
        {"question": "A113 appears in every Pixar movie.", "is_true": True},
        {"question": "Pumbaa in 'The Lion King' was the first character to fart in a Disney movie.", "is_true": True},
        {"question": "Walt Disney voiced Mickey Mouse for over 20 years.", "is_true": True},
        {"question": "The Genie in 'Aladdin' has a total of 10,000 years of confinement in his lamp.", "is_true": True},
        {"question": "'Beauty and the Beast' was the first animated film to win an Oscar for Best Picture.",
         "is_true": False},
        {"question": "Dory from 'Finding Nemo' suffers from short-term memory loss.", "is_true": True},
        {"question": "'Tangled' was the first full-length computer-animated fairy-tale adventure Disney movie.",
         "is_true": False},
        {"question": "The Prince in 'Snow White and the Seven Dwarfs' is named Henry.", "is_true": False},
        {"question": "Rapunzel is Disney's oldest princess.", "is_true": False},
        {"question": "The original name of 'The Lion King' was 'King of the Jungle'.", "is_true": True},
        {"question": "WALL-E stands for Waste Allocation Load Lifter: Earth-Class.", "is_true": True},
        {"question": "Boo's real name in 'Monsters, Inc.' is Mary.", "is_true": True},
        {"question": "Aurora speaks the least of all Disney Princesses.", "is_true": True},
        {"question": "Donald Duck's middle name is Fauntleroy.", "is_true": True},
        {"question": "The dog in 'Up' is named Doug.", "is_true": True},
        {"question": "Cinderella’s slippers are made of glass in the original movie.", "is_true": True},
        {"question": "Mulan has a pet dragon named Mushu.", "is_true": True},
        {"question": "The first Pixar movie was 'Toy Story'.", "is_true": True}
    ]

    def __init__(self, udp_port=13117):
        self.server_ip = self.get_server_ip()
        self.udp_port = udp_port
        self.tcp_port = self.find_free_port()
        self.server_name = 'BattleBitNetwork'  # Unique server name
        self.magic_cookie = 0xabcddcba
        self.message_type = 0x2
        self.clients = []  # List to store client information
        self.game_active = False
        self.game_start_timer = None
        self.broadcasting = True  # Flag to control UDP broadcasting
        self.lock = Lock()
        self.disqualified_players = set()
        self.flag_new_game = True
        self.stats = GameStatistics()  # Create an instance of GameStatistics

        self.current_question = None

        self.udp_socket = self.create_udp_socket()
        self.tcp_socket = self.create_tcp_socket()

    def create_udp_socket(self):
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            return udp_socket
        except socket.error as e:
            print(f"{self.ANSI_RED}Failed to create UDP socket: {e}{self.ANSI_RESET}")
            exit(1)

    def create_tcp_socket(self):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.bind((self.server_ip, self.tcp_port))
            tcp_socket.listen()
            return tcp_socket
        except socket.error as e:
            print(f"{self.ANSI_RED}Failed to create or bind TCP socket: {e}{self.ANSI_RESET}")
            exit(1)

    def get_server_ip(self):
        """Determine the server's IP address for client connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]


    def countdown(self):
        for i in reversed(range(1, 6)):  # Countdown from 5 to 1
            print(f"{self.ANSI_GREEN}{i}{self.ANSI_RESET}")
            for client in self.clients:
                try:
                    client['socket'].send(str(i).encode())
                except Exception as e:
                    print(f"{self.ANSI_RED}Failed to send to {client['name']}: {e}{self.ANSI_RESET}")
                    self.remove_client(client['socket'], client['name'])
            time.sleep(1)

    def is_port_in_use(self, port):
        """
        Check if a port is in use or not. Check if we can use the port.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def find_free_port(self, start=49000, end=65500):
        """
        Find a free port we can use.
        """
        for port in range(start, end + 1):
            if not self.is_port_in_use(port):
                return port
        raise IOError("No free port found.")


    def broadcast_udp_offers(self):
        message = struct.pack('!Ib32sH', self.magic_cookie, self.message_type, self.server_name.encode(), self.tcp_port)
        while self.broadcasting:
            try:
                self.udp_socket.sendto(message, ('<broadcast>', self.udp_port))
                print(f"{self.ANSI_YELLOW}ping{self.ANSI_RESET}")
                time.sleep(1)
            except Exception as e:
                print(f"{self.ANSI_RED}Error broadcasting UDP offer: {e}{self.ANSI_RESET}")

    def handle_client(self, client_socket, addr):
        player_name = client_socket.recv(1024).decode().strip()
        print(f"{self.ANSI_GREEN}player {player_name} connected from {addr}{self.ANSI_RESET}")
        with self.lock:
            self.clients.append({'socket': client_socket, 'name': player_name, 'active': True})

        # Record that the player has played a game
        self.stats.record_game_played(player_name)

        while True:
            try:
                answer = client_socket.recv(1024).decode().strip()
                print(f"{self.ANSI_MAGENTA}player {player_name} answered with {answer}{self.ANSI_RESET}")


                if player_name in self.disqualified_players:
                    continue  # Skip processing if player is already disqualified

                correct = self.current_question['is_true'] == (answer in ['Y', 'T', '1'])
                if correct:
                    self.stats.record_victory(player_name)
                    self.declare_winner(player_name)
                    break
                else:
                    self.disqualify_player(client_socket, player_name)
                    if len(self.disqualified_players) == len(self.clients):
                        message = "All the players was wrong:(, sending a new question:\n"
                        print(f"{self.ANSI_RED}{message}{self.ANSI_RESET}")
                        for client in self.clients:
                            try:
                                client['socket'].send(message.encode())
                            except Exception as e:
                                print(f"{self.ANSI_RED}Failed to send to {client['name']}: {e}{self.ANSI_RESET}")
                                self.remove_client(client['socket'], client['name'])
                        self.disqualified_players.clear()
                        self.start_game()
                    continue
            except:
                client_socket.close()
                self.remove_client(client_socket, player_name)
                self.broadcasting = True
                self.game_active = False
                self.flag_new_game = True
                message = f'player {player_name} has been disconnected from the game, Starting a new Game :)'
                print(f'{self.ANSI_MAGENTA}{message}{self.ANSI_RESET}')
                for client in self.clients:
                    try:
                        client['socket'].send(message.encode())
                    except Exception as e:
                        print(f"{self.ANSI_RED}Failed to send to {client['name']}: {e}{self.ANSI_RESET}")
                        self.remove_client(client['socket'], client['name'])

                threading.Thread(target=self.broadcast_udp_offers).start()
                self.accept_tcp_connections()
        # Save the stats after handling each client
        self.stats.save_stats()

    def remove_client(self, client_socket, player_name):
        with self.lock:
            self.clients = [client for client in self.clients if client['socket'] != client_socket]
            self.disqualified_players.discard(player_name)
            print(f"{self.ANSI_RED}Player {player_name} has been removed.{self.ANSI_RESET}")

    def declare_winner(self, player_name):
        message = f"{player_name} is correct! {player_name} wins!"
        summary_message = message + f"\n\nGame over!\nCongratulations to the winner: {player_name}"

        # Get the list of names of players who were in the current game
        current_game_player_names = [client['name'] for client in self.clients]

        stats_summary = self.stats.get_summary(current_game_player_names)
        summary_message_with_stats = summary_message + "\n\n" + stats_summary

        for client in self.clients:
            try:
                client['socket'].send(summary_message_with_stats.encode())
            except Exception as e:
                print(f"{self.ANSI_RED}Failed to send to {client['name']}: {e}{self.ANSI_RESET}")
                self.remove_client(client['socket'], client['name'])
        print(f"{self.ANSI_MAGENTA}{summary_message_with_stats}{self.ANSI_RESET}")
        self.reset_game()

    def disqualify_player(self, client_socket, player_name):
        message = f"{player_name} is incorrect and disqualified!"
        client_socket.send(message.encode())
        print(f"{self.ANSI_RED}{message}{self.ANSI_RESET}")
        self.disqualified_players.add(player_name)

    def start_or_restart_timer(self):
        if self.game_start_timer is not None:
            self.game_start_timer.cancel()
        self.game_start_timer = threading.Timer(10.0, self.start_game)
        self.game_start_timer.start()

    def accept_tcp_connections(self):
        print(f"{self.ANSI_YELLOW}TCP server listening on {self.server_ip}:{self.tcp_port}{self.ANSI_RESET}")
        while True:
            client_socket, addr = self.tcp_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            self.start_or_restart_timer()

    def start_game(self):
        if len(self.clients) < 2:
            message = "Not enough players to start the game. Waiting for more players..."
            print(f"{self.ANSI_BLUE}{message}{self.ANSI_RESET}")
            for client in self.clients:
                try:
                    client['socket'].send(message.encode())
                except Exception as e:
                    print(f"{self.ANSI_RED}Failed to send to {client['name']}: {e}{self.ANSI_RESET}")
                    self.remove_client(client['socket'], client['name'])
            self.start_or_restart_timer()
            return

        self.disqualified_players.clear()
        self.game_active = True
        self.broadcasting = False
        self.current_question = random.choice(self.disney_trivia_questions)
        if self.flag_new_game:
            message = f"\nWelcome to the {self.server_name} server, where we are answering trivia questions.\n"
            for client in self.clients:
                message += f"Player: {client['name']}\n"
            message += "get ready we start in 5 second:"
            print(f"{self.ANSI_GREEN}{message}{self.ANSI_RESET}")
            for client in self.clients:
                try:
                    client['socket'].send(message.encode())
                except Exception as e:
                    print(f"{self.ANSI_RED}Failed to send to {client['name']}: {e}{self.ANSI_RESET}")
                    self.remove_client(client['socket'], client['name'])
            message = ""
            self.countdown()
            self.flag_new_game = False
        else:
            message = f"Time up, sending a new question:\n"
        message += "==\n" + self.current_question["question"]
        for client in self.clients:
            try:
                client['socket'].send(message.encode())
            except Exception as e:
                print(f"{self.ANSI_RED}Failed to send to {client['name']}: {e}{self.ANSI_RESET}")
                self.remove_client(client['socket'], client['name'])
        print(f"{self.ANSI_MAGENTA}{message}{self.ANSI_RESET}")
        self.start_or_restart_timer()

    def reset_game(self):
        print(f"{self.ANSI_YELLOW}Game over, sending out offer requests...{self.ANSI_RESET}")
        self.broadcasting = True  # Ensure broadcasting resumes
        for client in self.clients:
            try:
                # Send a disconnection message before closing the socket
                disconnection_message = "Server disconnected, listening for offer requests..."
                client['socket'].send(disconnection_message.encode())
                client['socket'].close()
            except Exception as e:
                print(f"{self.ANSI_RED}Error closing connection for {client['name']}: {e}{self.ANSI_RESET}")
                self.remove_client(client['socket'], client['name'])
        # self.cleanup_resources()
        # self.reinitialize_components()
        self.clients.clear()
        self.disqualified_players.clear()
        self.broadcasting = True
        self.game_active = False
        self.flag_new_game = True
        self.run()


    def run(self):
        print(f"{self.ANSI_YELLOW}Server started, listening on IP address {self.server_ip}{self.ANSI_RESET}")
        threading.Thread(target=self.broadcast_udp_offers).start()
        self.accept_tcp_connections()

# Create and start the server
if __name__ == '__main__':
    server = Server()
    server.run()
