import socket
import struct
import time
from threading import Lock
import threading
import random
from Statistic import GameStatistics
from colors import colors

class Server:

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
        '''
        create UDP socket for future broadcasting
        '''
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            return udp_socket
        except socket.error as e:
            print(f"{colors.RED}Failed to create UDP socket: {e}{colors.RESET}")
            exit(1)

    def create_tcp_socket(self):
        '''
        create tcp socket for listening to Client connect request

        '''
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.bind((self.server_ip, self.tcp_port))
            tcp_socket.listen()
            return tcp_socket
        except socket.error as e:
            print(f"{colors.RED}Failed to create or bind TCP socket: {e}{colors.RESET}")
            exit(1)



    def get_server_ip(self):
        """Determine the server's IP address for client connections."""

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]


    def countdown(self):
        '''
        count down 5 sec before display the trivia question

        '''

        for i in reversed(range(1, 6)):  # Countdown from 5 to 1
            time.sleep(0.5)
            print(f"{colors.GREEN}{i}{colors.RESET}")
            self.sent_to_clients(i)
            time.sleep(0.5)
            if len(self.clients) < 2:
                break
        self.game_active = True



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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.server_ip, 0))
            return s.getsockname()[1]





    def broadcast_udp_offers(self):
        '''
        broadcast UDP request every 1 sec
        :return:
        '''

        message = struct.pack('!Ib32sH', self.magic_cookie, self.message_type, self.server_name.encode(), self.tcp_port)
        while self.broadcasting:
            try:
                self.udp_socket.sendto(message, ('<broadcast>', self.udp_port))   # sending the message request
                print(f"{colors.YELLOW}ping{colors.RESET}")
                time.sleep(1)
            except Exception as e:
                print(f"{colors.RED}Error broadcasting UDP offer: {e}{colors.RESET}")





    def sent_to_clients(self, message):
        '''
        broadcast function that sending message for all the clients
        :param message: any string
        '''

        for client in self.clients:
            try:
                client['socket'].send(str(message).encode())
            except Exception as e:
                print(f"{colors.RED}Failed to send to {client['name']}: {e}{colors.RESET}")





    def handle_client(self, client_socket, addr):
        '''
        handling client problem and messages

        :param client_socket: client_socket
        :param addr: address
        '''

        player_name = client_socket.recv(1024).decode().strip()
        print(f"{colors.BLUE}player {player_name} connected from {addr}{colors.RESET}")

        with self.lock:
            self.clients.append({'socket': client_socket, 'name': player_name, 'active': True})    # append the client to the active client list

        # Record that the player has played a game
        self.stats.record_game_played(player_name)

        while True:
            try:
                answer = client_socket.recv(1024).decode().strip()   # get some answer from the client
                if answer not in ['Y', 'N']:     # i.e the client disconnected or collapses
                    self.remove_client(client_socket, player_name)

                    if len(self.clients) < 2:
                        self.start_game()
                        break
                    else:
                         continue   # if there is more than 1 client in the game after some client disconnected or collapses

                print(f"{colors.MAGENTA}player {player_name} answered with {answer}{colors.RESET}")

                if player_name in self.disqualified_players:
                    continue  # Skip processing if player is already disqualified
                if self.game_active:   # prevent from clients to responses if the game is not active
                    correct = self.current_question['is_true'] == (answer in ['Y', 'T', '1'])
                    if correct:
                        self.stats.record_victory(player_name)
                        self.declare_winner(player_name)
                        break
                    else:
                        self.disqualify_player(client_socket, player_name)    # wrong answer -> client is disqualified
                        if len(self.disqualified_players) == len(self.clients):   # all the clients answer wrong answer -> broadcast new question
                            self.disqualified_players.clear()
                            self.start_game()
                        continue
            except Exception as e:
                print(f"{colors.RED}Error receiving data from {addr}: {e}{colors.RESET}")
                self.remove_client(client_socket, player_name)         # client disconnected or collapses
                if len(self.clients) < 2:
                    self.start_game()
                break
        # Save the stats after handling each client
        self.stats.save_stats()






    def remove_client(self, client_socket, player_name):
        '''
        remove client from the active client list and from disqualified clients list
        :param client_socket: client_socket
        :param player_name: player_name
        '''

        with self.lock:
            self.clients = [client for client in self.clients if client['socket'] != client_socket]
            self.disqualified_players.discard(player_name)
            print(f"{colors.RED}Player {player_name} has been removed.{colors.RESET}")




    def declare_winner(self, player_name):
        '''
        Sends all active clients a message and announces the winner
        show statistics details of the Clients
        reset the game and starting a new game
        :param player_name:player_name
        :return:
        '''

        message = f"{player_name} is correct! {player_name} wins!"
        summary_message = message + f"\n\nGame over!\nCongratulations to the winner: {player_name}"

        # Get the list of names of players who were in the current game
        current_game_player_names = [client['name'] for client in self.clients]

        stats_summary = self.stats.get_summary(current_game_player_names)
        summary_message_with_stats = summary_message + "\n\n" + stats_summary
        self.sent_to_clients(summary_message_with_stats)
        print(f"{colors.MAGENTA}{summary_message_with_stats}{colors.RESET}")
        self.reset_game()





    def disqualify_player(self, client_socket, player_name):
        '''
        disqualify player after giving wrong answer
        :param client_socket: client_socket
        :param player_name: player_name
        '''

        message = f"{player_name} is incorrect and disqualified!"
        client_socket.send(message.encode())
        print(f"{colors.RED}{message}{colors.RESET}")
        self.disqualified_players.add(player_name)  # add the client to the disqualified list of the current round




    def start_or_restart_timer(self):
        '''
        timer of 10 sec
        '''
        if self.game_start_timer is not None:
            self.game_start_timer.cancel()
        self.game_start_timer = threading.Timer(10.0, self.start_game)
        self.game_start_timer.start()




    def accept_tcp_connections(self):
        '''
        accept TCP connects from some Client that want to connect
        save the client socket and the client address
        create a thread for the client answer and response
        '''

        print(f"{colors.YELLOW}TCP server listening on {self.server_ip}:{self.tcp_port}{colors.RESET}")
        while True:
            client_socket, addr = self.tcp_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            self.start_or_restart_timer()  #reset the timer





    def start_game(self):
        '''
        game logic, check if there is more than 2 player and start the trivia game
        '''

        if len(self.clients) < 2:
            if self.game_active:    # if client disconnected or collapses while the game is running
                message = "Not enough players to continue the game. go back to waiting room..."
                print(f"{colors.BLUE}{message}{colors.RESET}")
                self.sent_to_clients(message)
                self.reset_game()

            message = "Not enough players to start the game. Waiting for more players..."
            print(f"{colors.BLUE}{message}{colors.RESET}")
            self.sent_to_clients(message)
            self.start_or_restart_timer()
            return

        self.disqualified_players.clear()

        self.broadcasting = False
        self.current_question = random.choice(self.disney_trivia_questions)
        if self.flag_new_game:
            message = f"\nWelcome to the {self.server_name} server, where we are answering trivia questions.\n"
            for client in self.clients:
                message += f"Player: {client['name']}\n"
            message += "get ready we start in 5 second:"
            print(f"{colors.YELLOW}{message}{colors.RESET}")
            self.sent_to_clients(message)
            message = ""
            self.countdown()
            if len(self.clients) < 2:    # if some client disconnected while the 5 sec countdown before starting the game
                msg = f"player has been disconnected, not enough players, go back to waiting room"
                print(f"{colors.RED}{msg}{colors.RESET}")
                self.sent_to_clients(msg)
                self.reset_game()
            self.flag_new_game = False
        else:
            message = f"Time up or All the players were wrong:(, sending a new question:\n"     # Times up or all the players were wrong
        message += "==\n" + "True or False: " + self.current_question["question"]
        self.sent_to_clients(message)
        print(f"{colors.MAGENTA}{message}{colors.RESET}")
        self.start_or_restart_timer()





    def reset_game(self):
        '''
        reset the game , close the sockets of all the clients and start a new game
        '''

        print(f"{colors.YELLOW}Game over, sending out offer requests...{colors.RESET}")
        self.broadcasting = True  # Ensure broadcasting resumes
        for client in self.clients:
            try:
                client['socket'].close()
            except Exception as e:
                print(f"{colors.RED}Error closing connection for {client['name']}: {e}{colors.RESET}")
                self.remove_client(client['socket'], client['name'])

        # reset all the lists and the flags
        self.clients.clear()
        self.disqualified_players.clear()
        self.broadcasting = True
        self.game_active = False
        self.flag_new_game = True
        self.run()




    def run(self):
        print(f"{colors.YELLOW}Server started, listening on IP address {self.server_ip}{colors.RESET}")
        threading.Thread(target=self.broadcast_udp_offers).start()
        self.accept_tcp_connections()



# Create and start the server
if __name__ == '__main__':
    server = Server()
    server.run()
