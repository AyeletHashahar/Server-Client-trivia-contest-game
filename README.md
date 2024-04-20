# Client - Server Trivia Game
## Project Overview
This Trivia Game Server is a part of a client-server application designed to host trivia games. It manages player connections, broadcasts trivia questions, evaluates answers, and determines game outcomes based on player responses. The server uses UDP for broadcasting its presence to potential clients and TCP for handling game logic and player interactions.
The implementation of this project has written with python and can be run only locally on the same network. 

## Features
* **UDP Broadcasting:** The server broadcasts its presence to the network, allowing clients to discover and connect to it.
* **TCP Connections:** Manages player connections and game interactions over TCP, ensuring reliable communication.
* **Trivia Logic:** Hosts trivia games by sending questions to connected clients, receiving their answers, and evaluating the outcomes.
* **Player Management:** Supports player disqualification for incorrect answers and allows for new rounds of trivia questions if all players are disqualified or fail to answer correctly.

## Getting Started
### Prerequisites
* Python 3.x installed on your server machine.
* Basic knowledge of Python programming.
* Understanding of TCP/UDP networking concepts.
### Installation
1. Clone the repository:
   *git clone [https://your-repository-url.git](https://github.com/AyeletHashahar/Server-Client-trivia-contest-game/tree/main)*
   
2. Navigate to the project directory:
   *cd trivia-game-server*

3. Run the server:
   *python server.py*
   
## Usage
Start the server by executing **python server.py**. Once running, it will begin broadcasting its presence via UDP and listen for incoming TCP connections from clients wanting to participate in the trivia game.

Clients must be designed to listen for the server's UDP broadcasts, connect via TCP, and interact with the game logic as implemented on the server.

## Contact
* Ayelet Hashahar Cohen - www.linkedin.com/in/ayelet-hashahar-cohen
* Tzuf lahan - www.linkedin.com/in/tzuf-lahan-962b76233

Project Link: https://github.com/AyeletHashahar/Server-Client-trivia-contest-game/tree/main
